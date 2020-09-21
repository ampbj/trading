import sys
sys.path.append('../')
from market_regime import market_regime_detection as mrd
import unittest
from unittest.mock import patch
import pandas
from pandas.util import testing

class Testmr(unittest.TestCase):
    @patch('market_regime.market_regime_detection.matplotlib.pyplot.show')
    def testmr(self, mock_pyplot):
        data = pandas.DataFrame(testing.makePeriodFrame()['A'])
        MR = mrd.Market_regime(data)
        MR.directional_change_fit().markov_switching_regression_fit().hidden_markov_model_fit()
        MR.plot_market_regime()
        mock_pyplot.assert_called_once()

if __name__ == '__main__':
    unittest.main()
