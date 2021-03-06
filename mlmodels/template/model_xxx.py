# coding: utf-8
"""
Generic template for new model.
Check parameters template in models_config.json

"model_pars":   { "learning_rate": 0.001, "num_layers": 1, "size": 6, "size_layer": 128, "output_size": 6, "timestep": 4, "epoch": 2 },
"data_pars":    { "data_path": "dataset/GOOG-year.csv", "data_type": "pandas", "size": [0, 0, 6], "output_size": [0, 6] },
"compute_pars": { "distributed": "mpi", "epoch": 10 },
"out_pars":     { "out_path": "dataset/", "data_type": "pandas", "size": [0, 0, 6], "output_size": [0, 6] }



"""
import inspect
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

VERBOSE = False

####################################################################################################
def os_module_path():
  current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
  parent_dir = os.path.dirname(current_dir)
  # sys.path.insert(0, parent_dir)
  return parent_dir


def os_file_path(data_path):
  from pathlib import Path
  data_path = os.path.join(Path(__file__).parent.parent.absolute(), data_path)
  print(data_path)
  return data_path


def os_package_root_path(filepath, sublevel=0, path_add=""):
  """
     get the module package root folder
  """
  from pathlib import Path
  path = Path(filepath).parent
  for i in range(1, sublevel + 1):
    path = path.parent
  
  path = os.path.join(path.absolute(), path_add)
  return path
# print("check", os_package_root_path(__file__, sublevel=1) )


def log(*s, n=0, m=1):
  sspace = "#" * n
  sjump = "\n" * m
  print(sjump, sspace, s, sspace, flush=True)


class to_namespace(object):
  def __init__(self, adict):
    self.__dict__.update(adict)

  def get(self, key):
    return self.__dict__.get(key)


def path_setup(out_folder="", sublevel=1, data_path="dataset/"):
    data_path = os_package_root_path(__file__, sublevel=sublevel, path_add=data_path)
    out_path = os.getcwd() + "/" + out_folder
    os.makedirs(out_path, exist_ok=True)
    model_path = out_path + "/model/"
    os.makedirs(model_path, exist_ok=True)

    log(data_path, out_path, model_path)
    return data_path, out_path, model_path



####################################################################################################
class Model:
  def __init__(self, model_pars=None, data_pars=None
               ):
    ### Model Structure        ################################
    self.model = None   #ex Keras model
    
    





def fit(model, data_pars={}, compute_pars={}, out_pars={}, out_pars={},  **kw):
  """

  :param model:    Class model
  :param data_pars:  dict of
  :param out_pars:
  :param compute_pars:
  :param kwargs:
  :return:
  """

  sess = None # Session type for compute
  Xtrain, Xtest, ytrain, ytest = None, None, None, None  # data for training.
  o = 0
  

  return model, sess



def metrics_model(model, **kw):
    """
       Return metrics of the model when fitted.
    """
    ddict = {}
    
    return ddict

    
        
        
        
def metrics(ytrue, ypred, yproba=None, model=None, sess=None, data_pars={}, out_pars={}, **kw):
    """
       Return metrics 
    """
    ddict = {}
    
    
    return ddict
  
  

def predict(model, sess=None, data_pars={}, out_pars={}, compute_pars={}, **kw):
  ##### Get Data ###############################################
  Xpred, ypred = None, None

  #### Do prediction
  ypred = model.model.fit(Xpred)

  ### Save Results
  
  
  ### Return val
  if compute_pars.get("return_pred_not") is not None :
    return ypred


  
  
def reset_model():
  pass



def save(model, path) :
  pass



def load(path) :
  model = Model()
  model.model = None
  return model   



####################################################################################################
def get_dataset(data_pars=None, **kw):
  """
    JSON data_pars to get dataset
    "data_pars":    { "data_path": "dataset/GOOG-year.csv", "data_type": "pandas",
    "size": [0, 0, 6], "output_size": [0, 6] },
  """

  if data_pars['train'] :
    Xtrain, Xtest, ytrain, ytest = None, None, None, None  # data for training.
    return Xtrain, Xtest, ytrain, ytest 

  else :
    Xtest, ytest = None, None  # data for training.
    return Xtest, ytest 







def get_params(choice="", data_path="dataset/", config_mode="test", **kw):
    if choice == "json":
        with open(data_path, encoding='utf-8') as config_f:
            config = json.load(config_f)
            c      = config[config_mode]

        model_pars, data_pars  = c[ "model_pars" ], c[ "data_pars" ]
        compute_pars, out_pars = c[ "compute_pars" ], c[ "out_pars" ]
        return model_pars, data_pars, compute_pars, out_pars


    if choice == "test01":
        log("#### Path params   ##########################################")
        data_path, out_path, model_path = path_setup(out_folder="", sublevel=1,
                                                     data_path="dataset/")
        data_pars    = {}
        model_pars   = {}
        compute_pars = {}
        out_pars     = {}

    return model_pars, data_pars, compute_pars, out_pars



################################################################################################
def test_global(data_path="dataset/", model_uri="model_tf/1_lstm.py", pars_choice="json", reset=True):
    ###loading the command line arguments
    #model_uri = "model_xxxx/yyyy.py"

    log("#### Module init   ############################################")
    from mlmodels.models import module_load
    module = module_load(model_uri)
    log(module)


    log("#### Loading params   ##############################################")
    model_pars, data_pars, compute_pars, out_pars = module.get_params(choice=pars_choice,
                                                                      data_path=data_path)


    log("#### Model init   ############################################")
    from mlmodels.models import model_create 
    model = model_create(module, model_pars)
    log(model)


    log("#### Fit   ########################################################")
    model, session = module.fit(model, data_pars, model_pars, compute_pars, out_pars )


    log("#### Predict   ####################################################")
    ypred = module.predict(model, session, data_pars, compute_pars, out_pars)
    print(ypred)


    log("#### Get  metrics   ################################################")
    metrics_val = module.metrics(model, data_pars, compute_pars, out_pars)


    log("#### Save/Load   ###################################################")
    module.save(model, out_pars['modelpath'])
    model2 = module.load(out_pars['modelpath'])
    #     ypred = predict(model2, data_pars, compute_pars, out_pars)
    #     metrics_val = metrics(model2, ypred, data_pars, compute_pars, out_pars)
    print(model2)




def test_global2(data_path="dataset/", model_uri="model_tf/1_lstm.py", pars_choice="json", reset=True):
    ###loading the command line arguments
    model_uri = "model_xxxx/yyyy.py"


    log("#### Module init   #################################################")
    from mlmodels.models import module_load
    module = module_load(model_uri)
    log(module)


    log("#### Loading params   ##############################################")
    from mlmodels.models import get_params as get_params_batch
    model_pars, data_pars, compute_pars, out_pars = get_params_batch(module, choice=pars_choice,
                                                                    data_path=data_path)

    log("#### Model init, fit   ############################################")
    from mlmodels.models import module_load_full 
    module, model = module_load_full(model_uri, model_pars)
    log(module, model)


    log("#### Fit   ########################################################")
    from mlmodels.models import fit as fit_batch
    model, session = fit_batch(model, module, compute_pars, data_pars, out_pars)


    log("#### Predict   ####################################################")
    ypred = predict_batch(model, module, session,  compute_pars, data_pars, out_pars)
    print(ypred)


    log("#### Mtrics   ################################################")
    from mlmodels.models import  metrics as metrics_batch 
    metrics_val = metrics_batch(model, module, session, compute_pars, data_pars,  out_pars)


    log("#### Save/Load   ###################################################")
    from mlmodels.models import load_batch, save_batch
    save_batch(model, module, session, out_pars['modelpath'])
    model2 = load_batch(out_pars['modelpath'])
    #     ypred = predict(model2, data_pars, compute_pars, out_pars)
    #     metrics_val = metrics(model2, ypred, data_pars, compute_pars, out_pars)
    print(model2)






def test(data_path="dataset/", pars_choice="json"):
    ### Local test

    log("#### Loading params   ##############################################")
    model_pars, data_pars, compute_pars, out_pars = get_params(choice=pars_choice,
                                                               data_path=data_path)

    log("#### Loading dataset   #############################################")
    Xtuple = get_dataset(data_pars)


    log("#### Model init, fit   #############################################")
    model = Model(model_pars, compute_pars)
    model = fit(model, data_pars, model_pars, compute_pars, out_pars)


    log("#### save the trained model  #######################################")
    save(model, out_pars["modelpath"])


    log("#### Predict   #####################################################")
    ypred = predict(model, data_pars, compute_pars, out_pars)


    log("#### metrics   #####################################################")
    metrics_val = metrics(model, ypred, data_pars, compute_pars, out_pars)
    print(metrics_val)


    log("#### Plot   ########################################################")


    log("#### Save/Load   ###################################################")
    save(model, out_pars['modelpath'])
    model2 = load(out_pars['modelpath'])
    #     ypred = predict(model2, data_pars, compute_pars, out_pars)
    #     metrics_val = metrics(model2, ypred, data_pars, compute_pars, out_pars)
    print(model2)



if __name__ == '__main__':
    VERBOSE = True
    test_path = os.getcwd() + "/mytest/"
    
    ### Local
    test(pars_choice="json")
    test(pars_choice="test01")

    ### Global mlmodels
    test_global(pars_choice="json", out_path= test_path,  reset=True)
