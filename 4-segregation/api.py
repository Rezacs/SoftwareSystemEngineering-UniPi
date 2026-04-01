"""Starts the REST API of the Segregation System using the communication controller."""

from src.communication_controller import CommunicationController


def main():
    controller = CommunicationController()
    controller.start_server()


if __name__ == "__main__":
    main()
