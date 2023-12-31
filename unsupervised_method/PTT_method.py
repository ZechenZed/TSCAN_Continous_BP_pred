import matplotlib.pyplot as plt
import numpy as np
import os
import global_align as ga
import cv2
import pandas as pd
from preprocess.video_preprocess import preprocess_raw_video_unsupervised, preprocess_finger
from unsupervised_method.CHROME import CHROME_DEHAAN
from unsupervised_method.GREEN import GREEN
from unsupervised_method.ICA_POH import ICA_POH
from scipy.signal import find_peaks, butter, filtfilt, medfilt
from unsupervised_method.POS_WANG import POS_WANG
from scipy.ndimage import gaussian_filter

os.environ['CUDA_VISIBLE_DEVICES'] = '1'


# print(os.cpu_count())

def video_process(device_type):
    if device_type == "local":
        env_path = 'C:/Users/Zed/Desktop/'
    elif device_type == 'disk':
        env_path = 'D:/'
    else:
        env_path = '/edrive2/zechenzh/'

    face_video_folder_path = env_path + 'Dual_Camera/face/'
    video_file_path = []
    for path in sorted(os.listdir(face_video_folder_path)):
        if os.path.isfile(os.path.join(face_video_folder_path, path)):
            video_file_path.append(path)
    video_file_path = video_file_path[3:4]
    print(video_file_path)

    for video in video_file_path:
        frames, fps = preprocess_raw_video_unsupervised(face_video_folder_path + video)
        finger_frames = preprocess_finger(env_path + 'Dual_Camera/finger/' + video)
        np.save(f'{env_path}/preprocessed_DC/face/{video[0:4]}.npy', frames)
        np.save(f'{env_path}/preprocessed_DC/finger/{video[0:4]}.npy', finger_frames)


def plotting(method_name, faceBVP, fingerBVP):
    dist_min = 240 / 2.5
    face_peaks, _ = find_peaks(faceBVP)
    finger_peaks, _ = find_peaks(fingerBVP)
    print(f'Number of face peaks:{len(face_peaks)} and Number of finger peaks{len(finger_peaks)}')
    plt.plot(face_peaks, faceBVP[face_peaks], 'o', label=f'{method_name} face peaks')
    plt.plot(finger_peaks, fingerBVP[finger_peaks], 'x', label=f'{method_name}finger peaks')
    plt.plot(faceBVP, label=f'{method_name}face')
    plt.plot(fingerBVP, label=f'{method_name}finger')
    plt.legend()
    plt.show()
    return face_peaks, finger_peaks


def normalization(bvp):
    bvp = bvp / max(abs(bvp))
    return bvp


def PTT(device_type):
    if device_type == "local":
        env_path = 'C:/Users/Zed/Desktop/preprocessed_DC/'
    elif device_type == 'disk':
        env_path = 'D:/preprocessed_DC/'
    else:
        env_path = '/edrive2/zechenzh/preprocessed_DC/'

    face_video_folder_path = env_path + 'face/'
    video_file_path = []
    for path in sorted(os.listdir(face_video_folder_path)):
        if os.path.isfile(os.path.join(face_video_folder_path, path)):
            video_file_path.append(path)
    print(video_file_path)

    ######################## Biodata Loading & Preprocessing ########################
    start_time = 5
    end_time = 45
    fs_bio = 1000
    start_frame_bio = start_time * fs_bio
    end_frame_bio = start_frame_bio + end_time * fs_bio
    biodata = np.array(pd.read_csv(env_path + 'bp/S55.csv')['SystolicBP'])[start_frame_bio:end_frame_bio]
    plt.plot(biodata, label='original')
    biodata = medfilt(biodata, 501)
    plt.plot(biodata, label='Median Filter')
    biodata = gaussian_filter(biodata,sigma=150)
    plt.plot(biodata, label='Median Filter + Gaussian Filter')
    plt.legend()
    plt.show()

    print('Loading Face Frames')
    face_frames = np.load(env_path + 'face/S055.npy')
    print('Loading Finger Frames')
    finger_frames = np.load(env_path + 'finger/S055.npy')

    fs = 240
    start_frame = start_time * fs
    end_frame = start_frame + end_time * fs
    face_frames = face_frames[start_frame:end_frame]
    finger_frames = finger_frames[start_frame:end_frame]

    ######################## Chrom ########################
    print('Processing CHROME')
    chrome_faceBVP = CHROME_DEHAAN(face_frames, fs)
    chrome_fingerBVP = CHROME_DEHAAN(finger_frames, fs)
    chrome_faceBVP = normalization(chrome_faceBVP)
    chrome_fingerBVP = normalization(chrome_fingerBVP)
    chrome_face_peaks, chrome_finger_peaks = plotting('Chrome', chrome_faceBVP, chrome_fingerBVP)
    ran = min(len(chrome_face_peaks), len(chrome_finger_peaks)) // 5
    PTT = []
    for i in range(ran):
        PTT.append(np.average(chrome_face_peaks[5 * i:5 * (i + 1)]) - \
                   np.average(chrome_finger_peaks[5 * i:5 * (i + 1)]))
    plt.plot(PTT)
    plt.show()

    ######################## ICA ########################
    print('Processing ICA')
    ICA_faceBVP = ICA_POH(face_frames, fs)
    ICA_fingerBVP = ICA_POH(finger_frames, fs)
    ICA_faceBVP = normalization(ICA_faceBVP)
    ICA_fingerBVP = normalization(ICA_fingerBVP)
    ICA_face_peaks, ICA_finger_peaks = plotting('ICA', ICA_faceBVP, ICA_fingerBVP)
    ran = min(len(ICA_face_peaks), len(ICA_finger_peaks)) // 5
    PTT = []
    for i in range(ran):
        PTT.append(np.average(ICA_face_peaks[5 * i:5 * (i + 1)]) - \
                   np.average(ICA_finger_peaks[5 * i:5 * (i + 1)]))
    plt.plot(PTT)
    plt.show()

    ######################## POS ########################
    print('Processing POS')
    POS_faceBVP = POS_WANG(face_frames, fs)
    POS_fingerBVP = POS_WANG(finger_frames, fs)
    POS_faceBVP = normalization(POS_faceBVP)
    POS_fingerBVP = normalization(POS_fingerBVP)
    POS_face_peaks, POS_finger_peaks = plotting('POS', POS_faceBVP, POS_fingerBVP)
    ran = min(len(POS_face_peaks), len(POS_finger_peaks)) // 5
    PTT = []
    for i in range(ran):
        PTT.append(np.average(POS_face_peaks[5 * i:5 * (i + 1)]) - \
                   np.average(POS_finger_peaks[5 * i:5 * (i + 1)]))
    plt.plot(PTT)
    plt.show()


if __name__ == '__main__':
    device_type = 'local'
    # video_process(device_type)
    PTT(device_type)
