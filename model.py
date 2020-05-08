import pandas as pd
import re
from os import system, listdir
from os.path import isfile, join
from random import shuffle
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from joblib import dump, load 
from scipy.sparse import save_npz, load_npz
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split
import numpy as np


'''
Make directories to store data and learning model for subsequent testing.
'''
# system("mkdir data_preprocessors")
# system("mkdir vectorized_data")
# system("mkdir csv")



def create_data_frame(folder):
    pos_folder = f'{folder}/pos'  # positive reviews
    neg_folder = f'{folder}/neg'  # negative reviews
    def get_files(folder):
        '''
        Get all files in the input folder
        '''
        return [join(folder, f) for f in listdir(folder) if isfile(join(folder, f))]

    def append_files_data(data_list, files, label):
        '''
        Appends to 'data_list' tuples of form (file content, label)
        for each file in 'files' input list
        '''
        for file in files:
            with open(file, 'r', encoding='utf-8') as f:
                text = f.read()
                data_list.append((text, label))

    pos_files = get_files(pos_folder)
    neg_files = get_files(neg_folder)

    data_list = []
    append_files_data(data_list, pos_files, 1)
    append_files_data(data_list, neg_files, 0)
    shuffle(data_list)

    text, label = tuple(zip(*data_list))
    # replacing line breaks with spaces
    text = list(map(lambda txt: re.sub('(<br\s*/?>)+', ' ', txt), text))

    return pd.DataFrame({'text': text, 'label': label})


# imdb_train = create_data_frame('aclImdb/train')
# imdb_test = create_data_frame('aclImdb/test')


# imdb_train.to_csv('csv/imdb_train.csv', index=False)
# imdb_test.to_csv('csv/imdb_test.csv', index=False)

imdb_train = pd.read_csv('csv/imdb_train.csv')
imdb_test = pd.read_csv('csv/imdb_test.csv')



# bigram_vectorizer = CountVectorizer(ngram_range=(1, 2))
# bigram_vectorizer.fit(imdb_train['text'].values)
# dump(bigram_vectorizer, 'data_preprocessors/bigram_vectorizer.joblib') # dump model so that we don't have to fit it again if we run the code again
bigram_vectorizer = load('data_preprocessors/bigram_vectorizer.joblib')


# X_train_bigram = bigram_vectorizer.transform(imdb_train['text'].values)
# save_npz('vectorized_data/X_train_bigram.npz', X_train_bigram) # dump matrix for future re-use
X_train_bigram = load_npz('vectorized_data/X_train_bigram.npz')

# bigram_tf_idf_transformer = TfidfTransformer()
# bigram_tf_idf_transformer.fit(X_train_bigram)
# dump(bigram_tf_idf_transformer, 'data_preprocessors/bigram_tf_idf_transformer.joblib')

bigram_tf_idf_transformer = load('data_preprocessors/bigram_tf_idf_transformer.joblib')

# X_train_bigram_tf_idf = bigram_tf_idf_transformer.transform(X_train_bigram)
# save_npz('vectorized_data/X_train_bigram_tf_idf.npz', X_train_bigram_tf_idf)
X_train_bigram_tf_idf = load_npz('vectorized_data/X_train_bigram_tf_idf.npz')

y_train = imdb_train['label'].values

# clf = SGDClassifier()
# clf.fit(X_train_bigram_tf_idf, y_train)
# system("mkdir classifiers")
# dump(clf, 'classifiers/sgd_classifier.joblib')
sgd_classifier = load('classifiers/sgd_classifier.joblib')

test_text = "Test classifier"
test = bigram_vectorizer.transform([test_text])
test = bigram_tf_idf_transformer.transform(test)


print(sgd_classifier.predict(test)[0])
