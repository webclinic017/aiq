from aiq.dataset import Dataset, Alpha158
from aiq.models import XGBModel, LGBModel

if __name__ == '__main__':
    handler = Alpha158()
    train_dataset = Dataset('./data', instruments='all', start_time='2021-08-30', end_time='2022-04-28', handler=handler, shuffle=True)
    valid_dataset = Dataset('./data', instruments='all', start_time='2022-04-29', end_time='2022-08-26', handler=handler)
    model_params = {
        'objective': 'mse',
        'learning_rate': 0.2,
        'colsample_bytree': 0.8879,
        'max_depth': 8,
        'num_leaves': 210,
        'subsample': 0.8789,
        'lambda_l1': 205.6999,
        'lambda_l2': 580.9768,
        'metric': 'rmse',
        'nthread': 4
    }
    model = LGBModel(feature_cols=handler.feature_names,
                     label_col=[handler.label_name],
                     model_params=model_params)
    model.fit(train_dataset=train_dataset, val_dataset=valid_dataset)
    result_dataset = model.predict(dataset=valid_dataset)
