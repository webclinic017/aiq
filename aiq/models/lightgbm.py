import os
import json

import lightgbm as lgb
import pandas as pd

from aiq.dataset import Dataset

from .base import BaseModel


class LGBModel(BaseModel):
    """LGBModel Model"""

    def fit(
        self,
        train_dataset: Dataset,
        val_dataset: Dataset = None,
        num_boost_round=1000,
        early_stopping_rounds=50,
        verbose_eval=20,
        eval_results=dict()
    ):
        train_df = train_dataset.to_dataframe()
        x_train, y_train = train_df[self._feature_cols].values, train_df[self.label_col].values
        dtrain = lgb.Dataset(x_train, label=y_train)
        evals = [dtrain]

        if val_dataset is not None:
            valid_df = val_dataset.to_dataframe()
            x_valid, y_valid = valid_df[self._feature_cols].values, valid_df[self.label_col].values
            dvalid = lgb.Dataset(x_valid, label=y_valid)
            evals.append(dvalid)

        self.model = lgb.train(
            self.model_params,
            train_set=dtrain,
            num_boost_round=num_boost_round,
            valid_sets=evals,
            valid_names=['train', 'valid'],
            early_stopping_rounds=early_stopping_rounds,
            verbose_eval=verbose_eval,
            evals_result=eval_results
        )
        eval_results["train"] = list(eval_results["train"].values())[0]
        if val_dataset is not None:
            eval_results["valid"] = list(eval_results["valid"].values())[0]

    def predict(self, dataset: Dataset):
        if self.model is None:
            raise ValueError("model is not fitted yet!")
        x_test = dataset.to_dataframe()[self._feature_cols].values
        predict_result = self.model.predict(x_test)
        dataset.add_column('PREDICTION', predict_result)
        return dataset

    def get_feature_importance(self, *args, **kwargs) -> pd.Series:
        """get feature importance
        Notes
        -------
            parameters reference:
                https://xgboost.readthedocs.io/en/latest/python/python_api.html#xgboost.Booster.get_score
        """
        return pd.Series(self.model.feature_importance(*args, **kwargs)).sort_values(ascending=False)

    def save(self, model_dir):
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        model_file = os.path.join(model_dir, 'model.json')
        self.model.save_model(model_file)

        model_params = {
            'feature_cols': self._feature_cols,
            'label_col': self._label_col,
            'model_params': self.model_params
        }
        with open(os.path.join(model_dir, 'model.params'), 'w') as f:
            json.dump(model_params, f)

    def load(self, model_dir):
        self.model = lgb.Booster(model_file=os.path.join(model_dir, 'model.json'))
        with open(os.path.join(model_dir, 'model.params'), 'r') as f:
            model_params = json.load(f)
            self._feature_cols = model_params['feature_cols']
            self._label_col = model_params['label_col']
            self.model_params = model_params['model_params']
