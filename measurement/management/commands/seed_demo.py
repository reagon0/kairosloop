# measurement/management/commands/seed_demo.py
"""
Seed demo data for KairosLoop.

One machine, one tool, one feature — the core loop.

Usage:
    python manage.py seed_demo          # Create demo data
    python manage.py seed_demo --clear  # Clear and recreate
"""

from django.core.management.base import BaseCommand

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
        self.stdout.write(self.style.SUCCESS('Demo data seeded.'))

    def clear_data(self):
        self.stdout.write('Clearing...')
        CompensationEvent.objects.all().delete()
        CompensationRule.objects.all().delete()
        Measurement.objects.all().delete()
        FeatureInput.objects.all().delete()
        Feature.objects.all().delete()
        ChannelConfig.objects.all().delete()
        GaugeConfig.objects.all().delete()
        ControllerConfig.objects.all().delete()
        Machine.objects.all().delete()

    def seed_data(self):
        # Machine
        machine, _ = Machine.objects.get_or_create(
            name='Tsugami B0205',
            defaults={
                'description': 'Swiss-type lathe',
                'location': 'Cell 5',
                'is_active': True,
            }
        )
        self.stdout.write(f'  Machine: {machine.name}')

        # Controller
        controller, _ = ControllerConfig.objects.get_or_create(
            name='Fanuc 32i',
            defaults={
                'machine': machine,
                'controller_type': 'fanuc',
                'protocol': 'TEST',
                'host': '192.168.1.100',
                'port': 8193,
                'timeout_ms': 1000,
                'active': True,
                'connected': False,
                'signal_cycle_complete': 'R100.0',
                'signal_master_request': 'R100.1',
                'signal_ready': 'R101.0',
                'signal_alarm': 'R101.1',
                'signal_pass': 'R101.3',
                'signal_fail': 'R101.4',
                'offset_method': 'WEAR',
                'offset_resolution': 0.001,
            }
        )
        self.stdout.write(f'  Controller: {controller.name}')

        # Gauge — 2 channels for opposing OD probes
        gauge, _ = GaugeConfig.objects.get_or_create(
            name='N1700 Module 1',
            defaults={
                'machine': machine,
                'driver_type': 'n1700',
                'dll_path': '',
                'use_64bit': True,
                'filter_level': 5,
                'active': True,
            }
        )

        ch0, _ = ChannelConfig.objects.get_or_create(
            gauge=gauge, channel_index=0,
            defaults={'name': 'OD Probe Left', 'enabled': True}
        )
        ch1, _ = ChannelConfig.objects.get_or_create(
            gauge=gauge, channel_index=1,
            defaults={'name': 'OD Probe Right', 'enabled': True}
        )
        self.stdout.write(f'  Gauge: {gauge.name} (2 channels)')

        # Feature — OD Diameter from two opposing probes
        feature, _ = Feature.objects.get_or_create(
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

        FeatureInput.objects.get_or_create(
            feature=feature, label='A',
            defaults={'channel_index': 0}
        )
        FeatureInput.objects.get_or_create(
            feature=feature, label='B',
            defaults={'channel_index': 1}
        )
        self.stdout.write(f'  Feature: {feature.name} = A + B, nominal={feature.nominal}, tol=±{feature.tolerance_upper}')

        # Compensation rule — Tool 1, X axis
        rule, _ = CompensationRule.objects.get_or_create(
            feature=feature,
            controller=controller,
            tool_number=1,
            defaults={
                'offset_register': 'D01',
                'offset_axis': 'X',
                'offset_direction': -1.0,
                'trigger_mode': 'THR',
                'trigger_threshold': 0.005,
                'sample_count': 1,
                'max_per_cycle': 0.010,
                'wear_limit': 0.100,
                'wear_limit_action': 'ALERT',
                'active': True,
                'accumulated_offset': 0.0,
            }
        )
        self.stdout.write(f'  Rule: {feature.name} -> T{rule.tool_number} {rule.offset_register} ({rule.offset_axis})')

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('One feature. One tool. One machine.'))
        self.stdout.write(f'  OD Diameter: nominal 25.400mm, tolerance ±0.010mm')
        self.stdout.write(f'  Tool 1 (D01 X): threshold 0.005, max/cycle 0.010, wear limit 0.100')