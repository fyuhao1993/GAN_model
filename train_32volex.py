from model import *
import numpy as np
import os
import dataIO
import utils


n_epochs = 10000

batch_size = 32
z_size = 200
alpha_d    = 0.0015
alpha_g    = 0.000025
beta  = 0.5
leak_value = 0.2
d_thresh   = 0.8
obj_ratio  = 0.5
# if os.path.exists('polygonData.npy'):
#     polygonBatch = np.load('polygonData.npy')
# else:
#     polygonBatch = loadData(1)

NUM_POLYGONS = 576
model_directory = './mlxFile32/'
train_sample_directory = './train_sample_32vox/'

weights,biases = {},{}

def generator(z,batch_size = batch_size,phase_train=True,reuse = False):
    strides = [1,2,2,2,1]
    with tf.variable_scope("gen", reuse=reuse):

        # z = tf.reshape(z, (batch_size, 1, 1, 1, z_size))
        # g_1 = tf.nn.conv3d_transpose(z, weights['wg1'], (batch_size, 4, 4, 4, 512), strides=[1, 1, 1, 1, 1],
        #                              padding="VALID")
        # g_1 = tf.nn.bias_add(g_1, biases['bg1'])
        # g_1 = tf.contrib.layers.batch_norm(g_1, is_training=phase_train)
        # g_1 = utils.lrelu(g_1)

        g_1 = tf.add(tf.matmul(z, weights['wg1']), biases['bg1'])
        g_1 = tf.reshape(g_1, [-1, 4, 4, 4, 512])
        g_1 = tf.contrib.layers.batch_norm(g_1, is_training=phase_train)
        # g_1 = tf.nn.relu(g_1)

        g_2 = tf.nn.conv3d_transpose(g_1, weights['wg2'], output_shape=[batch_size, 8, 8, 8, 256], strides=strides, padding="SAME")
        g_2 = tf.nn.bias_add(g_2, biases['bg2'])
        g_2 = tf.contrib.layers.batch_norm(g_2, is_training=phase_train)
        g_2 = tf.nn.relu(g_2)

        g_3 = tf.nn.conv3d_transpose(g_2, weights['wg3'], output_shape=[batch_size, 16, 16, 16, 128], strides=strides, padding="SAME")
        g_3 = tf.nn.bias_add(g_3, biases['bg3'])
        g_3 = tf.contrib.layers.batch_norm(g_3, is_training=phase_train)
        g_3 = tf.nn.relu(g_3)

        g_4 = tf.nn.conv3d_transpose(g_3, weights['wg4'], output_shape=[batch_size, 32, 32, 32, 1], strides=strides, padding="SAME")
        g_4 = tf.nn.bias_add(g_4, biases['bg4'])
        g_4 = tf.contrib.layers.batch_norm(g_4, is_training=phase_train)
        g_4 = tf.nn.sigmoid(g_4)
        #
        # g_5 = tf.nn.conv3d_transpose(g_4, weights['wg5'], output_shape=[batch_size, 64, 64, 64, 1], strides=strides, padding="SAME")
        # g_5 = tf.nn.bias_add(g_5, biases['bg5'])
        # g_5 = tf.nn.tanh(g_5)
    print(g_1, 'g1')
    print(g_2, 'g2')
    print(g_3, 'g3')
    print(g_4, 'g4')
    # print(g_5, 'g5')

    return g_4

def discriminator(inputs, phase_train=True, reuse=False):
    strides = [1, 2, 2, 2, 1]
    with tf.variable_scope("dis", reuse=reuse):
        d_1 = tf.nn.conv3d(inputs, weights['wd1'], strides=strides, padding="SAME")
        d_1 = tf.nn.bias_add(d_1, biases['bd1'])
        d_1 = tf.contrib.layers.batch_norm(d_1, is_training=phase_train)
        d_1 = utils.lrelu(d_1,leak_value)

        d_2 = tf.nn.conv3d(d_1, weights['wd2'], strides=strides, padding="SAME")
        d_2 = tf.nn.bias_add(d_2, biases['bd2'])
        d_2 = tf.contrib.layers.batch_norm(d_2, is_training=phase_train)
        d_2 = utils.lrelu(d_2,leak_value)

        d_3 = tf.nn.conv3d(d_2, weights['wd3'], strides=strides, padding="SAME")
        d_3 = tf.nn.bias_add(d_3, biases['bd3'])
        d_3 = tf.contrib.layers.batch_norm(d_3, is_training=phase_train)
        d_3 = utils.lrelu(d_3,leak_value)

        d_4 = tf.nn.conv3d(d_3, weights['wd4'], strides=strides, padding="SAME")
        d_4 = tf.nn.bias_add(d_4, biases['bd4'])
        d_4 = tf.contrib.layers.batch_norm(d_4, is_training=phase_train)
        d_4 = utils.lrelu(d_4,leak_value)

        # d_5 = tf.nn.conv3d(d_4, weights['wd5'], strides=[1, 1, 1, 1, 1], padding="VALID")
        # d_5 = tf.nn.bias_add(d_5, biases['bd5'])
        # d_5 = tf.nn.sigmoid(d_5)
        shape = d_4.get_shape().as_list()
        dim = np.prod(shape[1:])
        d_5 = tf.reshape(d_4, shape=[-1, dim])
        d_5 = tf.nn.sigmoid(tf.add(tf.matmul(d_5, weights['wd5']), biases['bd5']))

    print(d_1, 'd1')
    print(d_2, 'd2')
    print(d_3, 'd3')
    print(d_4, 'd4')
    print(d_5, 'd5')

    return d_5


def initialiseWeights():
    global weights
    xavier_init = tf.contrib.layers.xavier_initializer()

    # filter for deconv3d: A 5-D Tensor with the same type as value and shape [depth, height, width, output_channels, in_channels]
    weights['wg1'] = tf.get_variable("wg1", shape=[z_size,4*4*4*512], initializer=xavier_init)
    weights['wg2'] = tf.get_variable("wg2", shape=[4, 4, 4, 256, 512], initializer=xavier_init)
    weights['wg3'] = tf.get_variable("wg3", shape=[4, 4, 4, 128, 256], initializer=xavier_init)
    weights['wg4'] = tf.get_variable("wg4", shape=[4, 4, 4, 1, 128], initializer=xavier_init)
    # weights['wg5'] = tf.get_variable("wg5", shape=[4, 4, 4, 1, 64], initializer=xavier_init)

    weights['wd1'] = tf.get_variable("wd1", shape=[4, 4, 4, 1, 32], initializer=xavier_init)
    weights['wd2'] = tf.get_variable("wd2", shape=[4, 4, 4, 32, 64], initializer=xavier_init)
    weights['wd3'] = tf.get_variable("wd3", shape=[4, 4, 4, 64, 128], initializer=xavier_init)
    weights['wd4'] = tf.get_variable("wd4", shape=[2, 2, 2, 128, 256], initializer=xavier_init)
    weights['wd5'] = tf.get_variable("wd5", shape=[2*2*2*256, 1], initializer=xavier_init)
    return weights


def initialiseBiases():
    global biases
    zero_init = tf.zeros_initializer()

    biases['bg1'] = tf.get_variable("bg1", shape=[4*4*4*512], initializer=zero_init)
    biases['bg2'] = tf.get_variable("bg2", shape=[256], initializer=zero_init)
    biases['bg3'] = tf.get_variable("bg3", shape=[128], initializer=zero_init)
    biases['bg4'] = tf.get_variable("bg4", shape=[1], initializer=zero_init)
    # biases['bg5'] = tf.get_variable("bg5", shape=[1], initializer=zero_init)

    biases['bd1'] = tf.get_variable("bd1", shape=[32], initializer=zero_init)
    biases['bd2'] = tf.get_variable("bd2", shape=[64], initializer=zero_init)
    biases['bd3'] = tf.get_variable("bd3", shape=[128], initializer=zero_init)
    biases['bd4'] = tf.get_variable("bd4", shape=[256], initializer=zero_init)
    biases['bd5'] = tf.get_variable("bd5", shape=[1], initializer=zero_init)

    return biases
def trainGAN():
    weights,biases = initialiseWeights(),initialiseBiases()
    z_vector = tf.placeholder(shape=[batch_size, z_size], dtype=tf.float32)
    x_vector = tf.placeholder(shape=[batch_size, 32,32,32,1], dtype=tf.float32)

    net_g_train = generator(z_vector, phase_train=True, reuse=False)

    d_output_x = discriminator(x_vector, phase_train=True, reuse=False)
    d_output_x = tf.maximum(tf.minimum(d_output_x, 0.99), 0.01)
    summary_d_x_hist = tf.summary.histogram("d_prob_x", d_output_x)

    d_output_z = discriminator(net_g_train, phase_train=True, reuse=True)
    d_output_z = tf.maximum(tf.minimum(d_output_z, 0.99), 0.01)
    summary_d_z_hist = tf.summary.histogram("d_prob_z", d_output_z)

    # Compute the discriminator accuracy
    n_p_x = tf.reduce_sum(tf.cast(d_output_x > 0.5, tf.int32))
    n_p_z = tf.reduce_sum(tf.cast(d_output_z <= 0.5, tf.int32))
    d_acc = tf.divide(n_p_x + n_p_z, 2 * batch_size)


    # Compute the discriminator and generator loss
    d_loss = -tf.reduce_mean(tf.log(d_output_x) + tf.log(1 - d_output_z))
    g_loss = -tf.reduce_mean(tf.log(d_output_z))

    summary_d_loss = tf.summary.scalar("d_loss", d_loss)
    summary_g_loss = tf.summary.scalar("g_loss", g_loss)
    summary_n_p_z = tf.summary.scalar("n_p_z", n_p_z)
    summary_n_p_x = tf.summary.scalar("n_p_x", n_p_x)
    summary_d_acc = tf.summary.scalar("d_acc", d_acc)

    net_g_test = generator(z_vector, phase_train=False, reuse=True)
    para_g = list(np.array(tf.trainable_variables())[[0, 1, 4, 5, 8, 9, 12, 13]])
    para_d = list(np.array(tf.trainable_variables())[[14, 15, 16, 17, 20, 21, 24, 25]])  # ,28,29]])
    # para_g = [var for var in tf.trainable_variables() if any(x in var.name for x in ['wg', 'bg', 'gen'])]
    # para_d = [var for var in tf.trainable_variables() if any(x in var.name for x in ['wd', 'bd', 'dis'])]

    # only update the weights for the discriminator network
    optimizer_op_d = tf.train.AdamOptimizer(learning_rate=alpha_d, beta1=beta).minimize(d_loss, var_list=para_d)
    # only update the weights for the generator network
    optimizer_op_g = tf.train.AdamOptimizer(learning_rate=alpha_g, beta1=beta).minimize(g_loss, var_list=para_g)

    saver = tf.train.Saver(max_to_keep=50)
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        z_sample = np.random.normal(0, 0.33, size=[batch_size, z_size]).astype(np.float32)
        volumes = dataIO.getAll(train=True,cube_len=32)
        volumes = volumes[..., np.newaxis].astype(np.float)

        for epoch in range(n_epochs):
            idx = np.random.randint(len(volumes),size=batch_size)
            x = volumes[idx]
            z = np.random.normal(0,0.33,size=[batch_size,z_size]).astype(np.float32)

            #

            # for start, end in zip(
            #         range(0, len(volumes), batch_size),
            # #         range(batch_size, len(volumes), batch_size)):
            #     x = volumes[start:end].reshape(batch_size,64,64,64, 1)

            d_summary_merge = tf.summary.merge([summary_d_loss,
                                                summary_d_x_hist,
                                                summary_d_z_hist,
                                                summary_n_p_x,
                                                summary_n_p_z,
                                                summary_d_acc])

            summary_d, discriminator_loss = sess.run([d_summary_merge, d_loss],
                                                     feed_dict={z_vector: z, x_vector: x})

            summary_g, generator_loss = sess.run([summary_g_loss, g_loss], feed_dict={z_vector: z})
            # d_output_z, d_output_x = sess.run([d_acc, n_p_x, n_p_z],
            #                                 feed_dict={z_vector: z_sample, x_vector: next_polygon})

            # d_accuracy, n_x, n_z = sess.run([d_acc, n_p_x, n_p_z], feed_dict={z_vector: z, x_vector: x})
            # print('-epoch{}--n_p_x:{}--n_p_z:{}--'.format(
            #      epoch,n_x, n_z))
            #
            # if d_accuracy < d_thresh:
            #     sess.run([optimizer_op_d], feed_dict={z_vector: z, x_vector: x})
            #     print('Discriminator Training ', "epoch: ", epoch, ', d_loss:', discriminator_loss, 'g_loss:',
            #           generator_loss, "d_acc: ", d_accuracy)
            #
            # sess.run([optimizer_op_g], feed_dict={z_vector: z})
            # print('Generator Training ', "epoch: ", epoch, ', d_loss:', discriminator_loss, 'g_loss:',
            #       generator_loss, "d_acc: ", d_accuracy)

            if discriminator_loss <= 4.6 * 0.1:
                sess.run([optimizer_op_g], feed_dict={z_vector: z})
            elif generator_loss <= 4.6 * 0.1:
                sess.run([optimizer_op_d], feed_dict={z_vector: z, x_vector: x})
            else:
                sess.run([optimizer_op_d], feed_dict={z_vector: z, x_vector: x})
                sess.run([optimizer_op_g], feed_dict={z_vector: z})

            print("epoch: ", epoch, ', d_loss:', discriminator_loss, 'g_loss:', generator_loss)
            # output generated chairs
            if epoch % 500 == 10:
            # if epoch ==0:
                g_model = sess.run(net_g_test, feed_dict={z_vector: z_sample})
                if not os.path.exists(train_sample_directory):
                    os.makedirs(train_sample_directory)
                print('-----========-------=====-----------=====-------------')
                np.save(train_sample_directory+'/'+str(epoch)+'_model.npy', g_model)
                # g_model.save(train_sample_directory+'/'+str(epoch))
                # getMeshFromMatrix(g_model.reshape(batch_size,NUM_POLYGONS,9),train_sample_directory,epoch)
                # g_model.dump(train_sample_directory + '/' + str(epoch))

            if epoch % 500 == 10:
            # if epoch==0:
                if not os.path.exists(model_directory):
                    os.makedirs(model_directory)
                saver.save(sess, save_path=model_directory + '/' + str(epoch) + '.cptk')

if __name__ == '__main__':
    # is_dummy =

    trainGAN()





