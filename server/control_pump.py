import argparse
from arduino_controller import ArduinoController

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pump', type=int, required=True)
    parser.add_argument('--duration', type=int, required=True)
    args = parser.parse_args()

    controller = ArduinoController()
    controller.control_pump(args.pump, args.duration)
    controller.save_watering_event(args.pump, args.duration)

if __name__ == '__main__':
    main() 