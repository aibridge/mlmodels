import torch
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F

import re

import pandas as pd
from numpy.random import RandomState

import torchtext
from torchtext.data import Field
from torchtext.data import TabularDataset
from torchtext.vocab import GloVe
from torchtext.data import Iterator, BucketIterator
import torchtext.datasets

import spacy
import os
import json
import shutil

#########
# UTILS #
#########

def _train(m, device, train_itr, optimizer, epoch, max_epoch):
    m.train()
    corrects, train_loss = 0.0,0
    for batch in train_itr:
        text, target = batch.text, batch.label
        text = torch.transpose(text,0, 1)
        target.data.sub_(1)
        text, target = text.to(device), target.to(device)
        optimizer.zero_grad()
        logit = m(text)
        
        loss = F.cross_entropy(logit, target)
        loss.backward()
        optimizer.step()
        
        train_loss+= loss.item()
        result = torch.max(logit,1)[1]
        corrects += (result.view(target.size()).data == target.data).sum()
    
    size = len(train_itr.dataset)
    train_loss /= size 
    accuracy = 100.0 * corrects/size
  
    return train_loss, accuracy
    
def _valid(m, device, test_itr):
    m.eval()
    corrects, test_loss = 0.0,0
    for batch in test_itr:
        text, target = batch.text, batch.label
        text = torch.transpose(text,0, 1)
        target.data.sub_(1)
        text, target = text.to(device), target.to(device)
        
        logit = m(text)
        loss = F.cross_entropy(logit, target)

        
        test_loss += loss.item()
        result = torch.max(logit,1)[1]
        corrects += (result.view(target.size()).data == target.data).sum()
    
    size = len(test_itr.dataset)
    test_loss /= size 
    accuracy = 100.0 * corrects/size
    
    return test_loss, accuracy

def _get_device():
    # use GPU if it is available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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


def get_config_file():
    return os.path.join(
        os_package_root_path(__file__, 1),
        'config', 'model_tch', 'textcnn.json')


def get_data_file():
    return os.path.join(
        os_package_root_path(__file__), 'dataset', 'IMDB_Dataset.txt')


def split_train_valid(path_data, path_train, path_valid, frac=0.7):
    df = pd.read_csv(path_data)
    rng = RandomState()
    tr = df.sample(frac=0.7, random_state=rng)
    tst = df.loc[~df.index.isin(tr.index)]
    print("Spliting original file to train/valid set...")
    tr.to_csv(path_train, index=False)
    tst.to_csv(path_valid, index=False)


def clean_str(string):
    """
    Tokenization/string cleaning for all datasets except for SST.
    Original taken from https://github.com/yoonkim/CNN_sentence/blob/master/process_data.py
    """
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    string = re.sub(r"n\'t", " n\'t", string)
    string = re.sub(r"\'re", " \'re", string)
    string = re.sub(r"\'d", " \'d", string)
    string = re.sub(r"\'ll", " \'ll", string)
    string = re.sub(r",", " , ", string)
    string = re.sub(r"!", " ! ", string)
    string = re.sub(r"\(", " \( ", string)
    string = re.sub(r"\)", " \) ", string)
    string = re.sub(r"\?", " \? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string.strip()


def create_tabular_dataset(path_train, path_valid, 
                           lang='en', pretrained_emb='glove.6B.300d'):
    spacy_en = spacy.load(lang, disable=[
        'tagger', 'parser', 'ner', 'textcat'
        'entity_ruler', 'sentencizer', 
        'merge_noun_chunks', 'merge_entities',
        'merge_subtokens'])

    def tokenizer(text):
        return [tok.text for tok in spacy_en.tokenizer(text)]

    # Creating field for text and label
    TEXT = Field(sequential=True, tokenize=tokenizer, lower=True)
    LABEL = Field(sequential=False)

    print('Preprocessing the text...')
    # clean the text
    TEXT.preprocessing = torchtext.data.Pipeline(clean_str)

    print('Creating tabular datasets...It might take a while to finish!')
    train_datafield = [('text', TEXT), ('label', LABEL)]
    tabular_train = TabularDataset(
        path=path_train, format='csv',
        skip_header=True, fields=train_datafield)

    valid_datafield = [('text', TEXT), ('label', LABEL)]

    tabular_valid = TabularDataset(path=path_valid, 
                                   format='csv',
                                   skip_header=True,
                                   fields=valid_datafield)

    print('Building vocaulary...')
    TEXT.build_vocab(tabular_train, vectors=pretrained_emb)
    LABEL.build_vocab(tabular_train)

    return tabular_train, tabular_valid, TEXT.vocab


def create_data_iterator(tr_batch_size, val_batch_size, tabular_train,
                         tabular_valid, d):
    # Create the Iterator for datasets (Iterator works like dataloader)

    train_iter = Iterator(
        tabular_train,
        batch_size=tr_batch_size,
        device=d,
        sort_within_batch=False,
        repeat=False)

    valid_iter = Iterator(
        tabular_valid,
        batch_size=val_batch_size,
        device=d,
        sort_within_batch=False,
        repeat=False)
    return train_iter, valid_iter

#########
# MODEL #
#########

class TextCNN(nn.Module):

    def __init__(self, vocab_built, dim_channel, kernel_height, dropout_rate, num_class):
        kernel_wins = [int(x) for x in kernel_height]
        super(TextCNN, self).__init__()
        # load pretrained embedding in embedding layer.
        emb_dim = vocab_built.vectors.size()[1]
        self.embed = nn.Embedding(*vocab_built.vectors.shape)
        self.embed.weight.data.copy_(vocab_built.vectors)

        # Convolutional Layers with different window size kernels
        self.convs = nn.ModuleList([nn.Conv2d(1, dim_channel, (w, emb_dim)) for w in kernel_wins])
        # Dropout layer
        self.dropout = nn.Dropout(dropout_rate)

        # FC layer
        self.fc = nn.Linear(len(kernel_wins) * dim_channel, num_class)

    def forward(self, x):
        emb_x = self.embed(x)
        emb_x = emb_x.unsqueeze(1)

        con_x = [conv(emb_x) for conv in self.convs]

        pool_x = [F.max_pool1d(x.squeeze(-1), x.size()[2]) for x in con_x]
        
        fc_x = torch.cat(pool_x, dim=1)
        
        fc_x = fc_x.squeeze(-1)

        fc_x = self.dropout(fc_x)
        logit = self.fc(fc_x)
        return logit

Model = TextCNN

#############
# functions #
#############

def get_params(path=None, test=False):
    if path is None:
        path = get_config_file()
    with open(path, 'r') as f:
        config = json.load(f)
    if test:
        config = config.get('test')
    else:
        config = config.get('prod')
    model_pars = config.get('model_pars', dict())
    data_pars = config.get('data_pars', dict())
    compute_pars = config.get('compute_pars', dict())
    out_pars = config.get('out_pars', dict())
    return model_pars, data_pars, compute_pars, out_pars


def metric(model, test_iter, vocab, *args, **kwargs):
    device = _get_device()
    return _valid(model, device, test_iter)

def fit(model, train_iter, valid_iter, vocab, compute_pars, out_pars):
    lr = compute_pars['learning_rate']
    epochs = compute_pars["epochs"]
    device = _get_device()
    train_loss = []
    train_acc = []
    test_loss = []
    test_acc = []
    best_test_acc = -1
    optimizer = optim.Adam(model.parameters(), lr=lr)
    for epoch in range(1, epochs + 1):
        #train loss
        tr_loss, tr_acc = _train(model, device, train_iter, optimizer, epoch, epochs)
        print('Train Epoch: {} \t Loss: {} \t Accuracy: {}%'.format(epoch, tr_loss, tr_acc))
        
        ts_loss, ts_acc = _valid(model, device, valid_iter)
        print('Valid Epoch: {} \t Loss: {} \t Accuracy: {}%'.format(epoch, ts_loss, ts_acc))
        
        if ts_acc > best_test_acc:
            best_test_acc = ts_acc
            #save paras(snapshot)
            print("model saves at {}% accuracy".format(best_test_acc))
            torch.save(model.state_dict(),
                       os.path.join(out_pars["checkpointdir"],
                                    "best_accuracy"))
            
        train_loss.append(tr_loss)
        train_acc.append(tr_acc)
        test_loss.append(ts_loss)
        test_acc.append(ts_acc)

def get_dataset(data_pars, out_pars):
    device = _get_device()
    path = os.path.join(
        os_package_root_path(__file__, 1), data_pars['data_path'])
    frac = data_pars['frac']
    lang = data_pars['lang']
    pretrained_emb = data_pars['pretrained_emb']
    train_exists = os.path.isfile(out_pars['train_path'])
    valid_exists = os.path.isfile(out_pars['valid_path'])
    if not (train_exists and valid_exists) or data_pars['split_if_exists']:
        split_train_valid(
            path, out_pars['train_path'], out_pars['valid_path'], frac
        )
    trainset, validset, vocab = create_tabular_dataset(
        out_pars['train_path'], out_pars['valid_path'], lang, pretrained_emb)
    train_iter, valid_iter = create_data_iterator(
        data_pars['batch_size'], data_pars['val_batch_size'],
        trainset, validset, device
    )
    return train_iter, valid_iter, vocab

def test():
    model_pars, data_pars, compute_pars, out_pars = get_params(test=True)
    print("\n####### Preprocessing dataset... #############\n")
    train_iter, valid_iter, vocab = get_dataset(data_pars, out_pars)
    print("\n####### Creating model... ####################\n")
    model = Model(vocab_built=vocab, **model_pars)
    print("\n####### Fitting model... ####################\n")
    fit(model, train_iter, valid_iter, vocab, compute_pars, out_pars)
    print("\n####### Computing model metrics... ##########")
    data_pars['frac'] = 1
    test_iter, _, vocab = get_dataset(data_pars, out_pars)
    model = Model(vocab_built=vocab, **model_pars)
    test_loss, accuracy, = metric(model, test_iter, vocab,
                                  data_pars, out_pars)
    print(f"\nTest loss: {test_loss}, accuracy: {accuracy}")

def test2():
    pass

def save(model, path):
    return torch.save(model, path)

def load(path):
    return torch.load(path)

if __name__ == '__main__':
    test()
