from machine import Pin, UART
import time

class MotorControl:
    def __init__(self, tx_pin=4, rx_pin=5, baudrate=115200):
        self.uart = UART(1, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin)) # Init URART

    def clear_motor_faults(self):
        self.uart.write("sc\n") # Clear faults

    def feed_watchdog(self):
        self.uart.write("u 0\n") # Feed watchdog without setting anything

    def read_motor_position(self):
        self.uart.write("r axis0.pos_estimate\n") # Request pos
        time.sleep(0.1)
        if self.uart.any():
            response = self.uart.read()
            position_str = response.decode().strip().split('\r\n')[0] # Convert to correct format
            return float(position_str)
        return None # Error

    def set_torque(self, torque):
        self.uart.write(f"w axis0.config.torque_soft_max {torque}\n")
        self.uart.write(f"w axis0.config.torque_soft_min {-torque}\n")
        return f"New torque setpoint: {torque}"

    def read_motor_power(self):
        self.uart.write("r axis0.motor.electrical_power\n")
        time.sleep(0.1)
        if self.uart.any():
            response = self.uart.read()
            power_str = response.decode().strip().split('\r\n')[0]
            return float(power_str)
        return None

    def read_bus_voltage(self):
        self.uart.write("r vbus_voltage\n")
        time.sleep(0.1)
        if self.uart.any():
            response = self.uart.read()
            voltage_str = response.decode().strip().split('\r\n')[0]
            return float(voltage_str)
        return None

    def read_motor_faults(self):
        self.uart.write("r get_drv_fault\n")
        time.sleep(0.1)
        if self.uart.any():
            response = self.uart.read()
            position_str = response.decode().strip().split('\r\n')[0]
            return float(position_str)
        return None

    def home_motor(self):
        margin = 0.2
        self.set_torque(0.3) # Very soft
        self.clear_motor_faults()
        self.uart.write("w axis0.requested_state 8\n") # Closed loop control
        while True:
            position = self.read_motor_position() # Read axis0 position
            print(position)
            if position is not None:
                if position > margin: # Home counterclockwise
                    self.uart.write("v 0 -2\n")
                elif position < -margin: # Home clockwise
                    self.uart.write("v 0 2\n")
                else:
                    self.uart.write("w axis0.requested_state 1\n") # Return to idle
                    break
                self.feed_watchdog() # Feed watchdog during loop
            else:
                return False # Error reading data
        return True # Successful home

    def run_motor(self, torque):
        if self.home_motor():
            self.set_torque(torque)
            self.uart.write("w axis0.requested_state 8\n")
            self.uart.write("q 0 0\n")
            print("Motor is now holding torque")

    def stop_motor(self):
        self.uart.write("w axis0.requested_state 1\n")
        print("Motor has been stopped.")
