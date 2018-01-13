#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Train and evaluate a MLP."""

# core modules
import time
import yaml

# 3rd party modules
from sklearn.metrics import accuracy_score
import click
import numpy as np

# local modules
from lidtk.data import wili
from lidtk.classifiers import tfidf_features as feature_extractor_module
# import char_features
# from lidtk.classifiers.char_features import FeatureExtractor

model_name = "mlp-3layer-tfidf-50"
model = None


###############################################################################
# CLI                                                                         #
###############################################################################
@click.group(name='mlp')
def entry_point():
    """Use the character distribution language classifier."""
    pass


@entry_point.command(name='train', help=__doc__)
@click.option('--config',
              help='Load YAML configuration file')
def main(config):
    """Load data, train model and evaluate it."""
    with open(config, 'r') as stream:
        config = yaml.load(stream)
    main_loaded(config, wili, feature_extractor_module)


@entry_point.command(name='wili', help=__doc__)
@click.option('--result_file',
              default='cld2_results.txt', show_default=True,
              help='Where to store the predictions')
@click.option('--config',
              type=click.Path(exists=True),
              required=True,
              help='Load YAML configuration file')
def eval_wili_cli(result_file, config):
    """Load a model and evaluate it."""
    from lidtk.classifiers import eval_wili
    with open(config, 'r') as stream:
        config = yaml.load(stream)
    data = wili.load_data(config)
    xs = feature_extractor_module.get_features(config, data)
    # xs = char_features.get_features({}, data)
    for set_name in ['x_train', 'x_test', 'x_val']:
        data[set_name] = xs['xs'][set_name]
    shape = (data['x_train'].shape[1], )
    globals()['model'] = load_model(config, shape)
    eval_wili(result_file, predict)


def load_model(config, shape):
    """Load a model."""
    model = create_model(wili.n_classes, shape)
    return model


def main_loaded(config, data_module, feature_extractor_module):
    """
    Load data, train model and evaluate it.

    Parameters
    ----------
    config : dict
    data_module : Python module
    feature_extractor_module : Python module
    """
    data = data_module.get_data()
    optimizer = get_optimizer({'optimizer': {'initial_lr': 0.0001}})
    model.compile(loss='categorical_crossentropy',
                  optimizer=optimizer,
                  metrics=['accuracy'])
    t0 = time.time()
    model.fit(data['x_train'], data['y_train'],
              batch_size=32,
              epochs=20,
              validation_data=(data['x_val'], data['y_val']),
              shuffle=True,
              # callbacks=callbacks
              )
    t1 = time.time()
    # res = get_tptnfpfn(model, data)

    t2 = time.time()
    model.save("{}.h5".format(model_name))
    preds = model.predict(data['x_test'])
    y_pred = np.argmax(preds, axis=1)
    y_true = np.argmax(data['y_test'], axis=1)
    print(("{clf_name:<30}: {acc:>4.2f}% in {train_time:0.2f}s "
           "train / {test_time:0.2f}s test")
          .format(clf_name="Random",
                  acc=(1. / 211),
                  train_time=0.00,
                  test_time=0.00))
    print(("{clf_name:<30}: {acc:>4.2f}% in {train_time:0.2f}s "
           "train / {test_time:0.2f}s test")
          .format(clf_name="MLP",
                  acc=(accuracy_score(y_true=y_true,
                                      y_pred=y_pred) * 100),
                  train_time=(t1 - t0),
                  test_time=(t2 - t1)))


def predict(text):
    """Predict the language of a text."""
    preds = model.predict(text)
    return preds


def create_model(nb_classes, input_shape):
    """Create a MLP model."""
    # from keras.layers import Dropout
    from keras.layers import Activation, Input
    from keras.layers import Dense
    from keras.models import Model

    input_ = Input(shape=input_shape)
    x = input_
    x = Dense(512, activation='relu')(x)
    x = Dense(nb_classes)(x)
    x = Activation('softmax')(x)
    model = Model(inputs=input_, outputs=x)
    return model


def get_optimizer(config):
    """Return an optimizer."""
    from keras.optimizers import Adam
    lr = config['optimizer']['initial_lr']
    optimizer = Adam(lr=lr)  # Using Adam instead of SGD to speed up training
    return optimizer
