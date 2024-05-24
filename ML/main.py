import numpy as np
import pandas as pd
import warnings
from sklearn.svm import SVC
import statsmodels.api as sm
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split,GridSearchCV
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree  import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn import tree
from sklearn import svm
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import GaussianNB
from sklearn import metrics
from sklearn.metrics import confusion_matrix
from sklearn.metrics import RocCurveDisplay
from itertools import cycle
from sklearn.model_selection import GridSearchCV
import joblib

Trained_Data = pd.read_csv("NSL-KDD/KDDTrain+.txt" , sep = "," , encoding = 'utf-8')
Tested_Data  = pd.read_csv("NSL-KDD/KDDTest+.txt" , sep = "," , encoding = 'utf-8')

Columns = (['duration','protocol_type','service','flag','src_bytes','dst_bytes','land','wrong_fragment','urgent','hot',
            'num_failed_logins','logged_in','num_compromised','root_shell','su_attempted','num_root','num_file_creations',
            'num_shells','num_access_files','num_outbound_cmds','is_host_login','is_guest_login','count','srv_count',
            'serror_rate','srv_serror_rate','rerror_rate','srv_rerror_rate','same_srv_rate','diff_srv_rate','srv_diff_host_rate',
            'dst_host_count','dst_host_srv_count','dst_host_same_srv_rate','dst_host_diff_srv_rate','dst_host_same_src_port_rate',
            'dst_host_srv_diff_host_rate','dst_host_serror_rate','dst_host_srv_serror_rate','dst_host_rerror_rate',
            'dst_host_srv_rerror_rate','attack','level'])

Trained_Data.columns = Columns
Tested_Data.columns  = Columns

columns = ['duration', 'protocol_type', 'service', 'src_bytes', 'dst_bytes', 'count', 'srv_count', 'attack']
Trained_Data = Trained_Data[columns]
Tested_Data = Tested_Data[columns]

print(Trained_Data.head(5))

# changing attack labels to their respective attack class
def change_label(df):
    df['attack'] = df['attack'].replace(['apache2','back','land','neptune','mailbomb','pod','processtable','smurf','teardrop','udpstorm','worm'],'Dos')
    df['attack'] = df['attack'].replace(['ftp_write','guess_passwd','httptunnel','imap','multihop','named','phf','sendmail','snmpgetattack','snmpguess','spy','warezclient','warezmaster','xlock','xsnoop'],'R2L')
    df['attack'] = df['attack'].replace(['ipsweep','mscan','nmap','portsweep','saint','satan'],'Probe')
    df['attack'] = df['attack'].replace(['buffer_overflow','loadmodule','perl','ps','rootkit','sqlattack','xterm'],'U2R')
    
change_label(Trained_Data)
change_label(Tested_Data)
print(Trained_Data.head(5))



# # label encoding (0,1,2,3,4) multi-class labels (Dos,normal,Probe,R2L,U2R)
# # LE = LabelEncoder()
attack_LE= LabelEncoder()
Trained_Data['attack'] = attack_LE.fit_transform(Trained_Data["attack"])
joblib.dump(attack_LE, 'label.joblib')
Tested_Data['attack'] = attack_LE.fit_transform(Tested_Data["attack"])


Trained_Data.drop_duplicates(subset=None, keep="first", inplace=True)
Tested_Data.drop_duplicates(subset=None, keep="first", inplace=True)

Trained_Data = pd.get_dummies(Trained_Data, columns=['protocol_type','service'],prefix="",prefix_sep="")
print(Trained_Data.columns)
joblib.dump(Trained_Data.columns, 'dummy_columns.joblib')

Tested_Data = pd.get_dummies(Tested_Data,columns=['protocol_type','service'],prefix="",prefix_sep="")

X_train = Trained_Data.drop('attack', axis = 1)

X_test = Tested_Data.drop('attack', axis = 1)

Y_train = Trained_Data['attack']
Y_test = Tested_Data['attack']

X_train_train,X_test_train ,Y_train_train,Y_test_train = train_test_split(X_train, Y_train, test_size= 0.25 , random_state=42)
X_train_test,X_test_test,Y_train_test,Y_test_test = train_test_split(X_test, Y_test, test_size= 0.25 , random_state=42)

Ro_scaler = RobustScaler()
X_train_train = Ro_scaler.fit_transform(X_train_train) 
joblib.dump(Ro_scaler, 'scaler.joblib')
X_test_train= Ro_scaler.transform(X_test_train)
X_train_test = Ro_scaler.fit_transform(X_train_test) 
X_test_test= Ro_scaler.transform(X_test_test)

max_depth= [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    
Parameters={ 'max_depth': max_depth}

def GridSearch(Model_Abb, Parameters, X_train, Y_train):
    Grid = GridSearchCV(estimator=Model_Abb, param_grid= Parameters, cv = 3, n_jobs=-1)
    Grid_Result = Grid.fit(X_train, Y_train)
    Model_Name = Grid_Result.best_estimator_
    
    return (Model_Name)

RF= RandomForestClassifier()
GridSearch(RF, Parameters, X_train_train, Y_train_train)
RF.fit(X_train_train, Y_train_train)
print(RF.score(X_train_train, Y_train_train))
print(RF.score(X_test_train, Y_test_train))
joblib.dump(RF, 'model.joblib')