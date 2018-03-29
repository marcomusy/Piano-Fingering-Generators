import numpy as np
import tensorflow as tf
import time
import pickle
import EvaluatePhrase
from LSTM_network import initNet, initBeam, initArgMax
from Utils import elapsed, generateNewState, generateNewStateBi
from parameters import *

input_list = pickle.load(open("../Datasets/processed/test_input_list_4_bi.pkl", "rb"))
label_list = pickle.load(open("../Datasets/processed/test_label_list_4_bi.pkl", "rb"))

x, _, keep_prob, pred = initNet(BIRNN)
onehot_holder, top_2_holder = initBeam()
onehot_holder_argmax, argmax_holder = initArgMax()
init = tf.global_variables_initializer()

saver = tf.train.Saver()

start_time = time.time()
# Launch the graph
with tf.Session() as session:
    if BIRNN:
    	saver.restore(session, "./models/bi_model_4/bi_model_4.ckpt")
    else:
    	saver.restore(session, "./models/uni_model_4/uni_model_4.ckpt")
    total_absTrue = 0
    total_absFalse = 0
    total_notGood = 0
    total_interval_len = 0
    print_finger_res = []
    for i in range(len(input_list)):
        test_interval = input_list[i]
        test_finger = label_list[i]
        init_state = [test_finger[0], test_interval[0], test_finger[1], test_interval[1], test_finger[2], test_interval[2], test_finger[3], test_interval[3], test_interval[4]]
        test_step = 0
        generate_step = len(test_interval)
        temp_finger_res = []
        
        while test_step < generate_step - (BLOCK_LENGTH):
            np_init_state = np.reshape(np.array(init_state), [-1, N_INPUT, 1])
            onehot_pred_test = session.run(pred, feed_dict={x: np_init_state, keep_prob: 1})
            
            # top_2 = session.run(top_2_holder, feed_dict={onehot_holder: onehot_pred_test[0]})
            # finger_pred_first = top_2[0]+1
            # finger_pred_second = top_2[1]+1
            
            finger_pred = session.run(argmax_holder, feed_dict={onehot_holder_argmax: onehot_pred_test})
            finger_pred = finger_pred[0] + 1 
            
            # uni_beam
            # finger_combo = [init_state[-2], finger_pred_first]
            # if EvaluatePhrase.qualityCheck(init_state[-1], finger_combo):
            #     finger_combo = [init_state[-2], finger_pred_second]
            #     if EvaluatePhrase.qualityCheck(init_state[-1], finger_combo):
            #         finger_pred = finger_pred_first
            #     else:
            #         finger_pred = finger_pred_second
            # else:
            #     finger_pred = finger_pred_first
            
            # bi_beam
            # finger_combo = [init_state[-3], finger_pred_first]
            # if EvaluatePhrase.qualityCheck(init_state[-2], finger_combo):
            #     finger_combo = [init_state[-3], finger_pred_second]
            #     if EvaluatePhrase.qualityCheck(init_state[-2], finger_combo):
            #         finger_pred = finger_pred_first
            #     else:
            #         finger_pred = finger_pred_second
            # else:
            #     finger_pred = finger_pred_first

            print(str(init_state) + "->" + str(finger_pred))
            temp_finger_res += [finger_pred]
            if test_step < generate_step - BLOCK_LENGTH - 1:
                if BIRNN:
                    init_state = generateNewStateBi(init_state, finger_pred, test_interval[test_step+BLOCK_LENGTH+1], False)
                else:
                    init_state = generateNewState(init_state, finger_pred, test_interval[test_step+BLOCK_LENGTH], False)
            test_step+=1
        temp_finger_res = [test_finger[-1]] + temp_finger_res
        print('number of notes: '+str(len(temp_finger_res)))
        if len(print_finger_res) == 0:
            print_finger_res = temp_finger_res
        elif len(print_finger_res) > len(temp_finger_res):
            print_finger_res = temp_finger_res
        # print(len(test_finger[BLOCK_LENGTH-1:]))
        # print(len(test_interval[BLOCK_LENGTH-1:]))
        absTrue, absFalse, notGood = EvaluatePhrase.main(test_interval[BLOCK_LENGTH-1:-1], temp_finger_res, test_finger[BLOCK_LENGTH-1:-1])
        total_absTrue += absTrue
        total_absFalse += absFalse
        total_notGood += notGood
        total_interval_len += (generate_step - (BLOCK_LENGTH-1))
        print('absolute acc: ' + str(absTrue), 'absolute wrong: ' + str(absFalse), 'not ideal: ' + str(notGood))
        print("Elapsed time: ", elapsed(time.time() - start_time))
        print("Testing finished")
    print('absolute acc: ' + str(total_absTrue/float(total_interval_len+len(input_list))), \
          'absolute false: ' + str(total_absFalse/float(total_interval_len)), \
          'not ideal: ' + str(total_notGood/float(total_interval_len)))
    print print_finger_res
