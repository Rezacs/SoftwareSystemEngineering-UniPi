from segregation.orchestrator import SegregationSystemOrchestrator


def main():
    result = SegregationSystemOrchestrator().run()
    print(result)


if __name__ == "__main__":
    main()
