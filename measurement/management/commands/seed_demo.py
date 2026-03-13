# measurement/management/commands/seed_demo.py
"""
Seed demo data for testing KairosLoop without hardware.

Usage:
    python manage.py seed_demo          # Create demo data
    python manage.py seed_demo --clear  # Clear and recreate
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from controller.models import Machine, ControllerConfig
from measurement.models import (
    GaugeConfig, ChannelConfig, Feature, FeatureInput, 
    Measurement, ToleranceMode, FeatureType, Unit
)
from compensation.models import CompensationRule, CompensationEvent


class Command(BaseCommand):
    help = 'Seed demo data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_data()
        
        self.seed_data()
        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully!'))

    def clear_data(self):
        """Clear all existing data."""
        self.stdout.write('Clearing existing data...')
        CompensationEvent.objects.all().delete()
        CompensationRule.objects.all().delete()
        Measurement.objects.all().delete()
        FeatureInput.objects.all().delete()
        Feature.objects.all().delete()
        ChannelConfig.objects.all().delete()
        GaugeConfig.objects.all().delete()
        ControllerConfig.objects.all().delete()
        Machine.objects.all().delete()
        self.stdout.write('  Cleared.')

    def seed_data(self):
        """Create demo data."""
        
        # =====================================================================
        # MACHINE
        # =====================================================================
        self.stdout.write('Creating machine...')
        machine, _ = Machine.objects.get_or_create(
            name='Tsugami Swiss #3',
            defaults={
                'description': 'Demo Swiss-type lathe for testing',
                'location': 'Building A, Cell 5',
                'is_active': True,
            }
        )
        self.stdout.write(f'  ✓ Machine: {machine.name}')

        # =====================================================================
        # CONTROLLER
        # =====================================================================
        self.stdout.write('Creating controller...')
        controller, _ = ControllerConfig.objects.get_or_create(
            name='Fanuc 32i (Test Mode)',
            defaults={
                'machine': machine,
                'controller_type': 'Fanuc',
                'protocol': 'TEST',  # Test mode, no real connection
                'host': '192.168.1.100',
                'port': 8193,
                'timeout_ms': 1000,
                'active': True,
                'connected': False,
                # Inbound signals
                'signal_cycle_complete': 'R100.0',
                'signal_master_request': 'R100.1',
                'signal_part_present': 'R100.2',
                'signal_tool_change': 'R100.3',
                # Outbound signals
                'signal_ready': 'R101.0',
                'signal_alarm': 'R101.1',
                'signal_measuring': 'R101.2',
                'signal_pass': 'R101.3',
                'signal_fail': 'R101.4',
                # Offset settings
                'offset_method': 'WEAR',
                'offset_resolution': 0.001,
                'offset_write_delay_ms': 50,
            }
        )
        self.stdout.write(f'  ✓ Controller: {controller.name}')

        # =====================================================================
        # GAUGE
        # =====================================================================
        self.stdout.write('Creating gauge and channels...')
        gauge, _ = GaugeConfig.objects.get_or_create(
            name='N1700 Module 1',
            defaults={
                'machine': machine,
                'driver_type': 'n1700',
                'dll_path': '',
                'use_64bit': True,
                'filter_level': 5,  # 32 samples
                'active': True,
            }
        )
        self.stdout.write(f'  ✓ Gauge: {gauge.name}')

        # Create 4 channels
        channel_configs = [
            {'index': 0, 'name': 'OD Probe Left'},
            {'index': 1, 'name': 'OD Probe Right'},
            {'index': 2, 'name': 'Face Probe'},
            {'index': 3, 'name': 'TIR Probe'},
        ]
        
        channels = []
        for cfg in channel_configs:
            ch, _ = ChannelConfig.objects.get_or_create(
                gauge=gauge,
                channel_index=cfg['index'],
                defaults={
                    'name': cfg['name'],
                    'enabled': True,
                }
            )
            channels.append(ch)
            self.stdout.write(f'    ✓ CH{cfg["index"]+1}: {cfg["name"]}')

        # =====================================================================
        # FEATURES
        # =====================================================================
        self.stdout.write('Creating features...')

        # Feature 1: OD Diameter (opposing probes, A + B)
        od_feature, _ = Feature.objects.get_or_create(
            name='OD Diameter',
            defaults={
                'description': 'Outside diameter from opposing probes',
                'feature_type': FeatureType.DIAMETER,
                'part_name': 'Shaft',
                'part_number': 'SH-001',
                'formula': 'A + B',
                'tolerance_mode': ToleranceMode.BILATERAL,
                'nominal': 25.400,
                'tolerance_upper': 0.010,
                'tolerance_lower': -0.010,
                'warning_percent': 80,
                'unit': Unit.MM,
                'resolution': 4,
                'active': True,
            }
        )
        # Add inputs
        FeatureInput.objects.get_or_create(
            feature=od_feature, label='A',
            defaults={'channel_index': 0}
        )
        FeatureInput.objects.get_or_create(
            feature=od_feature, label='B',
            defaults={'channel_index': 1}
        )
        self.stdout.write(f'  ✓ Feature: {od_feature.name} (formula: {od_feature.formula})')

        # Feature 2: Length (single probe)
        length_feature, _ = Feature.objects.get_or_create(
            name='Face Length',
            defaults={
                'description': 'Face-to-datum length',
                'feature_type': FeatureType.LENGTH,
                'part_name': 'Shaft',
                'part_number': 'SH-001',
                'formula': 'A',
                'tolerance_mode': ToleranceMode.BILATERAL,
                'nominal': 50.000,
                'tolerance_upper': 0.025,
                'tolerance_lower': -0.025,
                'warning_percent': 75,
                'unit': Unit.MM,
                'resolution': 4,
                'active': True,
            }
        )
        FeatureInput.objects.get_or_create(
            feature=length_feature, label='A',
            defaults={'channel_index': 2}
        )
        self.stdout.write(f'  ✓ Feature: {length_feature.name} (formula: {length_feature.formula})')

        # Feature 3: TIR (limit mode)
        tir_feature, _ = Feature.objects.get_or_create(
            name='Runout TIR',
            defaults={
                'description': 'Total indicator reading for runout',
                'feature_type': FeatureType.TIR,
                'part_name': 'Shaft',
                'part_number': 'SH-001',
                'formula': 'A',
                'tolerance_mode': ToleranceMode.LIMIT,
                'nominal': None,
                'tolerance_upper': 0.015,
                'tolerance_lower': None,
                'warning_percent': 70,
                'unit': Unit.MM,
                'resolution': 4,
                'active': True,
            }
        )
        FeatureInput.objects.get_or_create(
            feature=tir_feature, label='A',
            defaults={'channel_index': 3}
        )
        self.stdout.write(f'  ✓ Feature: {tir_feature.name} (formula: {tir_feature.formula})')

        # =====================================================================
        # COMPENSATION RULES
        # =====================================================================
        self.stdout.write('Creating compensation rules...')

        # Rule for OD Diameter
        od_rule, _ = CompensationRule.objects.get_or_create(
            feature=od_feature,
            controller=controller,
            tool_number=1,
            defaults={
                'offset_register': 'D01',
                'offset_axis': 'X',
                'offset_direction': -1.0,  # Negative = compensate
                'trigger_mode': 'THR',  # Threshold mode
                'trigger_threshold': 0.005,
                'sample_count': 1,
                'max_per_cycle': 0.010,
                'wear_limit': 0.100,
                'wear_limit_action': 'ALERT',
                'active': True,
                'accumulated_offset': 0.0,
            }
        )
        self.stdout.write(f'  ✓ Rule: {od_feature.name} → T{od_rule.tool_number} ({od_rule.offset_register})')

        # Rule for Length
        length_rule, _ = CompensationRule.objects.get_or_create(
            feature=length_feature,
            controller=controller,
            tool_number=2,
            defaults={
                'offset_register': 'D02',
                'offset_axis': 'Z',
                'offset_direction': -1.0,
                'trigger_mode': 'THR',
                'trigger_threshold': 0.008,
                'sample_count': 1,
                'max_per_cycle': 0.015,
                'wear_limit': 0.150,
                'wear_limit_action': 'ALERT',
                'active': True,
                'accumulated_offset': 0.0,
            }
        )
        self.stdout.write(f'  ✓ Rule: {length_feature.name} → T{length_rule.tool_number} ({length_rule.offset_register})')

        # =====================================================================
        # SAMPLE MEASUREMENTS (optional history)
        # =====================================================================
        self.stdout.write('Creating sample measurements...')
        
        import random
        from datetime import timedelta

        now = timezone.now()
        
        for i in range(10):
            # OD measurement (simulate slight drift)
            drift = 0.002 * i + random.uniform(-0.003, 0.003)
            channel_values = {0: 12.700 + drift, 1: 12.700 + drift + random.uniform(-0.001, 0.001)}
            
            Measurement.create_from_channels(
                feature=od_feature,
                channel_values=channel_values,
                source='seed_demo'
            )
            
            # Length measurement
            channel_values = {2: 50.000 + random.uniform(-0.015, 0.015)}
            Measurement.create_from_channels(
                feature=length_feature,
                channel_values=channel_values,
                source='seed_demo'
            )
            
            # TIR measurement
            channel_values = {3: abs(random.uniform(0, 0.012))}
            Measurement.create_from_channels(
                feature=tir_feature,
                channel_values=channel_values,
                source='seed_demo'
            )

        self.stdout.write(f'  ✓ Created 30 sample measurements')

        # =====================================================================
        # SUMMARY
        # =====================================================================
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('DEMO DATA SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'  Machine:      {machine.name}')
        self.stdout.write(f'  Controller:   {controller.name} ({controller.protocol})')
        self.stdout.write(f'  Gauge:        {gauge.name} ({len(channels)} channels)')
        self.stdout.write(f'  Features:     {Feature.objects.count()}')
        self.stdout.write(f'  Comp Rules:   {CompensationRule.objects.count()}')
        self.stdout.write(f'  Measurements: {Measurement.objects.count()}')
        self.stdout.write('')
        self.stdout.write('Test URLs:')
        self.stdout.write('  http://localhost:8000/              Dashboard')
        self.stdout.write('  http://localhost:8000/measurement/  Features')
        self.stdout.write('  http://localhost:8000/measurement/gauge/  Gauges')
        self.stdout.write('  http://localhost:8000/compensation/ Rules')
        self.stdout.write('  http://localhost:8000/controller/   Controllers')
        self.stdout.write('  http://localhost:8000/admin/        Admin')
