# test_n1700.py

from devices.n1700 import N1700

# Make sure DLLs are in the same directory or provide path
gauge = N1700(dll_path="path/to/N1700.dll")

try:
    num_modules, num_channels = gauge.initialize()
    print(f"Found {num_modules} modules, {num_channels} channels")
    
    # List modules
    for i in range(num_modules):
        module = gauge.get_module(i)
        print(f"Module {i}: {module['type_name']} (SN: {module['serial_no']})")
    
    # List channels
    for i in range(num_channels):
        channel = gauge.get_channel(i)
        print(f"Channel {i}: {channel['port_type'].name}")
    
    # Read values
    print("\nReading values (press Ctrl+C to stop)...")
    while True:
        for i in range(num_channels):
            value = gauge.poll_data(i)
            print(f"  Ch{i}: {value:+.6f} mm")
        print()
        import time
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Stopped")
finally:
    gauge.close()
    