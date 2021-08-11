class ProgressBar:
    """This class implements a progress bar for the whole application.
    """

    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance

    def __init__(self):

        self._progressWidget = None

    def setProgressWidget(self, progressWidget):

        self._progressWidget = progressWidget

    def reset(self, nSteps):
        """Initializes the progress bar.

        Args:
            n_steps (int): the total number of steps of the task to monitor
        """

        if not self._progressWidget:
            return

        try:
            self._progressWidget.setMinimum(0)
            self._progressWidget.setMaximum(nSteps)
        except AttributeError:
            return

    def update(self, step):
        """Updates the progress bar.

        Args:
            step (int): the step
        """

        if not self._progressWidget:
            return

        try:
            self._progressWidget.setValue(step)
        except AttributeError:
            return

# Create an instance of the progrss bar (singleton)
progressBar = ProgressBar()
