
from Data.learningPlot import LearningPlot
class LearningPlotView:
    def display_learning_plot(self, learning_plot: LearningPlot) -> None:
        print("[LearningPlotView] Displaying learning plot.")
        print(f"  MSE values     : {learning_plot.mse}")
        print(f"  Epoch counts   : {learning_plot.number_of_epochs}")
        print(f"  Approved       : {learning_plot.approve}")
        print(f"  Set epochs     : {learning_plot.set_epochs}")