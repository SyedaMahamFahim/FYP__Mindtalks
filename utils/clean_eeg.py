import mne
import pickle
import numpy as np

from utils.Events_analysis import Event_correction, add_condition_tag, add_block_tag
from utils.Events_analysis import check_baseline_tags, delete_trigger
from utils.Events_analysis import cognitive_control_check, standardize_labels
from utils.Data_extractions import extract_subject_from_bdf
from utils.Utilitys import ensure_dir


# Processing Variables

# Root where the raw data are stored
root_dir = '../uploads/'

# Root where the structured data will be saved
# It can be changed and saved in other direction
save_dir = root_dir + "derivatives/"

# #################### Filtering
# Cut-off frequencies
Low_cut = 0.5
High_cut = 100

# Notch filter in 50Hz
Notch_bool = True

# Downsampling rate
DS_rate = 4

# #################### ICA
# If False, ICA is not applied
ICA_bool = True
ICA_Components = None
ica_random_state = 23
ica_method = 'infomax'
max_pca_components = None
fit_params = dict(extended=True)

# #################### EMG Control
low_f = 1
high_f = 20
# Slide window design
# Window len (time in sec)
window_len = 0.5
# slide window step (time in sec)
window_step = 0.05

# Threshold for EMG control
std_times = 3

# Baseline
t_min_baseline = 0
t_max_baseline = 15

# Trial time
t_min = 1
t_max = 3.5

# Events ID
# Trials tag for each class.
# 31 = Arriba / Up
# 32 = Abajo / Down
# 33 = Derecha / Right
# 34 = Izquierda / Left
event_id = dict(Arriba=31, Abajo=32, Derecha=33, Izquierda=34)

# Baseline id
baseline_id = dict(Baseline=13)

# Report initialization
report = dict(Age=0, Gender=0, Recording_time=0, Ans_R=0, Ans_W=0)

# Montage
Adquisition_eq = "biosemi128"
# Get montage
montage = mne.channels.make_standard_montage(Adquisition_eq)

# Extern channels
Ref_channels = ['EXG1', 'EXG2']

# Gaze detection
Gaze_channels = ['EXG3', 'EXG4']

# Blinks detection
Blinks_channels = ['EXG5', 'EXG6']

# Mouth Moving detection
Mouth_channels = ['EXG7', 'EXG8']

# Demographic information
Subject_age = [56, 50, 34, 24, 31, 29, 26, 28, 35, 31]
Subject_gender = ['F', 'M', 'M', 'F', 'F', 'M', 'M', 'F', 'M', 'M']

def process_subject_session(local_file_path, subject_no, session_no):

    N_S = int(subject_no)
    N_B = int(session_no)

    print(type(N_S))
    print(type(N_B))

    # Initialize report
    report = dict()
    
    # Get Age and Gender
    report['Age'] = Subject_age[N_S-1]
    report['Gender'] = Subject_gender[N_S-1]

    print('Subject: ' + str(N_S))
    print('Session: ' + str(N_B))

    # Load data from BDF file
    rawdata, Num_s = extract_subject_from_bdf(local_file_path, N_S, N_B)

    print('Data loaded')
    print('Referencing')

    # Referencing
    rawdata.set_eeg_reference(ref_channels=Ref_channels)

    print('Montage')
    if Notch_bool:
        # Notch filter
        rawdata = mne.io.Raw.notch_filter(rawdata, freqs=50)

    print(rawdata.info)

    # Filtering raw data
    print('Filtering')
    rawdata.filter(Low_cut, High_cut)

    # Get events
    # Subject 10 on Block 1 have a spurious trigger
    if (N_S == 10 and N_B == 1):
        events = mne.find_events(rawdata, initial_event=True,
                                 consecutive=True, min_duration=0.002)
    else:
        events = mne.find_events(rawdata, initial_event=True,
                                 consecutive=True)

    events = check_baseline_tags(events)

    # Check and Correct event
    events = Event_correction(events=events)

    # Replace the raw events with the new corrected events
    rawdata.event = events

    report['Recording_time'] = int(np.round(rawdata.last_samp/rawdata.info['sfreq']))

    # Cognitive Control
    report['Ans_R'], report['Ans_W'] = cognitive_control_check(events)

    # Save report
    file_path = save_dir + Num_s + '/ses-0' + str(N_B)
    ensure_dir(file_path)

    pickle_file_name = file_path + '/' + Num_s + '_ses-0'+str(N_B)+'_report.pkl'
    with open(pickle_file_name, 'wb') as output:
        pickle.dump(report, output, pickle.HIGHEST_PROTOCOL)

    # EXG
    picks_eog = mne.pick_types(rawdata.info, eeg=False, stim=False, include=['EXG1', 'EXG2', 'EXG3', 'EXG4','EXG5', 'EXG6', 'EXG7', 'EXG8'])
    
    epochsEOG = mne.Epochs(rawdata, events, event_id=event_id, tmin=-0.5,
                               tmax=4, picks=picks_eog, preload=True,
                               detrend=0, decim=DS_rate)

    # Save EOG
    eog_file_name = file_path + '/' + Num_s + '_ses-0' + str(N_B) + '_exg-epo.fif'
    epochsEOG.save(eog_file_name, fmt='double',
                       split_size='2GB', overwrite=True)

    # Baseline
    t_baseline = (events[events[:, 2] == 14, 0]-events[events[:, 2] == 13, 0]) / rawdata.info['sfreq']
    t_baseline = t_baseline[0]
    Baseline = mne.Epochs(rawdata, events, event_id=baseline_id, tmin=0,
                              tmax=round(t_baseline), picks='all',
                              preload=True, detrend=0, decim=DS_rate,
                              baseline=None)

    # Save Baseline
    baseline_file_name = file_path + '/' + Num_s + '_ses-0' + str(N_B) + '_baseline-epo.fif'
    Baseline.save(baseline_file_name, fmt='double',
                      split_size='2GB', overwrite=True)

    # Epoching and decimating EEG
    picks_eeg = mne.pick_types(rawdata.info, eeg=True,
                                   exclude=['EXG1', 'EXG2', 'EXG3', 'EXG4',
                                            'EXG5', 'EXG6', 'EXG7', 'EXG8'],
                                   stim=False)

    epochsEEG = mne.Epochs(rawdata, events, event_id=event_id, tmin=-0.5,
                               tmax=4, picks=picks_eeg, preload=True,
                               detrend=0, decim=DS_rate, baseline=None)

    # ICA Processing
    if ICA_bool:
        # Get a full trials including EXG channels
        picks_vir = mne.pick_types(rawdata.info, eeg=True,
                                   include=['EXG1', 'EXG2', 'EXG3', 'EXG4',
                                            'EXG5', 'EXG6',
                                            'EXG7', 'EXG8'],
                                   stim=False)
        epochsEEG_full = mne.Epochs(rawdata, events, event_id=event_id,
                                    tmin=-0.5, tmax=4,
                                    picks=picks_vir, preload=True,
                                    detrend=0, decim=DS_rate,
                                    baseline=None)

        # Liberate Memory for ICA processing
        del rawdata

        # Creating the ICA object
        ica = mne.preprocessing.ICA(n_components=ICA_Components,
                                    random_state=ica_random_state,
                                    method=ica_method,
                                    fit_params=fit_params)

        # Fit ICA, calculate components
        ica.fit(epochsEEG)
        ica.exclude = []

        # Detect sources by correlation
        exg_inds_EXG3, scores_ica = ica.find_bads_eog(epochsEEG_full,
                                                      ch_name='EXG3')
        ica.exclude.extend(exg_inds_EXG3)

        # Detect sources by correlation
        exg_inds_EXG4, scores_ica = ica.find_bads_eog(epochsEEG_full,
                                                      ch_name='EXG4')
        ica.exclude.extend(exg_inds_EXG4)

        # Detect sources by correlation
        exg_inds_EXG5, scores_ica = ica.find_bads_eog(epochsEEG_full,
                                                      ch_name='EXG5')
        ica.exclude.extend(exg_inds_EXG5)

        # Detect sources by correlation
        exg_inds_EXG6, scores_ica = ica.find_bads_eog(epochsEEG_full,
                                                      ch_name='EXG6')
        ica.exclude.extend(exg_inds_EXG6)

        # Detect sources by correlation
        exg_inds_EXG7, scores_ica = ica.find_bads_eog(epochsEEG_full,
                                                      ch_name='EXG7')
        ica.exclude.extend(exg_inds_EXG7)

        # Detect sources by correlation
        exg_inds_EXG8, scores_ica = ica.find_bads_eog(epochsEEG_full,
                                                      ch_name='EXG8')
        ica.exclude.extend(exg_inds_EXG8)

        print("Applying ICA")
        ica.apply(epochsEEG)

    # Save EEG
    eeg_file_name = file_path + '/' + Num_s + '_ses-0' + str(N_B) + '_eeg-epo.fif'
    epochsEEG.save(eeg_file_name, fmt='double',
                   split_size='2GB', overwrite=True)

    # Standardize and save events
    events = add_condition_tag(events)
    events = add_block_tag(events, N_B=N_B)
    events = delete_trigger(events)
    events = standardize_labels(events)

    # Save events
    events_file_name = file_path + '/' + Num_s + '_ses-0' + str(N_B) + '_events.dat'
    events.dump(events_file_name)

    return eog_file_name, baseline_file_name, pickle_file_name, eeg_file_name, events_file_name





# # Example call
# local_file = '/content/drive/MyDrive/FYPD_Dataset/sub-02/ses-02/eeg/sub-02_ses-02_task-innerspeech_eeg.bdf'
# process_subject_session(local_file, 2, 2)


    
#     return pickle_file_name


# local_file='/content/drive/MyDrive/FYPD_Dataset/sub-02/ses-01/eeg/sub-02_ses-01_task-innerspeech_eeg.bdf'
# process_subject_session(local_file, 2,1)

# Example usage
# process_subject_session(1, 1)  # Process data for Subject 1, Session 1
