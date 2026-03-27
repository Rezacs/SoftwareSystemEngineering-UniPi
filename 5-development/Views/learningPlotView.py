# Views/learningPlotView.py
from Data.learningPlot import LearningPlot

class LearningPlotView:
    def display_learning_plot(self, plot: LearningPlot) -> None:
        print("[LearningPlotView] Learning curve (epoch → MSE):")
        for epoch, mse in zip(plot.number_of_epochs, plot.mse):
            print(f"  Epoch {epoch:>4}: MSE={mse:.6f}")
        print(f"  Approved: {plot.approve}")