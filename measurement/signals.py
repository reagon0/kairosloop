# measurement/signals.py
"""
Django signals for the measurement app.

These signals allow other apps (compensation, logging, etc.) to react
to measurement events without tight coupling.
"""

from django.dispatch import Signal

# Emitted after a measurement is captured and saved
# Sender: CaptureService
# Kwargs: measurement (Measurement instance), feature_result (dict)
measurement_captured = Signal()

# Emitted after a batch of measurements is captured
# Sender: CaptureService  
# Kwargs: measurements (list of Measurement instances), capture_result (CaptureResult)
capture_completed = Signal()
