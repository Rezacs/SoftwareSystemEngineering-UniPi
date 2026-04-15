"""View component for displaying a learning curve to the console."""

from Data.learningPlot import LearningPlot


class LearningPlotView:
    """Renders a LearningPlot object as formatted console output."""

    def display_learning_plot(self, plot: LearningPlot) -> None:
        """Print the per-epoch loss values and approval status."""
        print("[LearningPlotView] Learning curve (epoch → loss):")
        for epoch, mse in zip(plot.number_of_epochs, plot.mse):
            print(f"  Epoch {epoch:>4}: loss={mse:.6f}")
        print(f"  Approved: {plot.approve}")