import tensorflow as tf
from tensorflow.keras.layers import Layer
import numpy as np

class Adjacency(Layer): 

    '''
        This layer calculates the learned adjacency matrices upto `power` hops.
    '''     
    
    def __init__(self, n_features=50, max_nodes=50):
        super(Adjacency, self).__init__()
        self.max_nodes = max_nodes
        self.n_features = n_features
        self.input_units = max_nodes * max_nodes
    
    def build(self, input_shape=(50, 50)): #NOTE: input_shape is required arg
                                           #      and is not used in code

        # using power 2 for the adjacency operator;
        # the number of weight matrices and the `power+1` needs to be the same
        
        # initialize 2 weight matrices for each adjacency matrices since we
        # will be making an MLP with one hidden layer

        # weights for the 0'th power adjacency matrix
        self.w0_1 = self.add_weight(shape=(self.input_units, self.input_units),
                                initializer='random_normal',
                                trainable=True, name='w0_1')
        self.w0_2 = self.add_weight(shape=(self.input_units, self.input_units),
                                initializer='random_normal',
                                trainable=True, name='w0_2')
        
        # weights for the 1'th power adjacency matrix
        self.w1_1 = self.add_weight(shape=(self.input_units, self.input_units),
                                initializer='random_normal',
                                trainable=True, name='w1_1')
        self.w1_2 = self.add_weight(shape=(self.input_units, self.input_units),
                                initializer='random_normal',
                                trainable=True, name='w1_2')

        # weights for the 2'th power adjacency matrix
        self.w2_1 = self.add_weight(shape=(self.input_units, self.input_units),
                                initializer='random_normal',
                                trainable=True, name='w2_1')
        self.w2_2 = self.add_weight(shape=(self.input_units, self.input_units),
                                initializer='random_normal',
                                trainable=True, name='w2_2')

    def call(self, inputs):  # NOTE: input_list contains a list of 
                             #       adjacency matrices and the node vec
                             #       matrix
        '''
            Generates adjacency matrices that consolidate the neighborhood
            information upto 2 walks. 

            Input:
                adj_list, 
                list of adjacency matrices as generated by 
                Graph Operators layer

                node_vec, 
                2d numpy array
                a matrix having feature vectors for each node in the graph

        '''
        adj_list = inputs[:-1]
        node_vec = inputs[-1]

        assert len(adj_list) == 3, f'The `adj_list` passed to the layer does \
            not contain 3 adjacency operators. Received `adj_list` of length: \
                {len(adj_list)}.'

        # the following assertions assume that each adjacency matrix in the 
        # list has the same shape
        try:
            assert adj_list[0].shape[0] == self.w0.shape[0], f'The number of rows \
                of the adjacency matrix and weight matrix does not match. /n\
                    Adjacency Shape: {adj_list.shape}\nWeight Matrix Shape: \
                        {self.w0.shape}.'

            assert adj_list[0].shape[0] == self.w0.shape[1], f'The number of \
                columns of the adjacency matrix and weight matrix does not match./n\
                    Adjacency Shape: {adj_list.shape}\nWeight Matrix Shape: \
                        {self.w0.shape}.'
        except:
            print("Error 87 layer")
        
        # remove singleton dimensions
        adj_0 = tf.squeeze(adj_list[0])
        adj_1 = tf.squeeze(adj_list[1])
        adj_2 = tf.squeeze(adj_list[2])
        node_vec = tf.squeeze(node_vec)

        # acquire shape for later use
        shape = adj_0.shape

        adj_0 = self._learn_adjacencies(adj_0, node_vec)
        adj_1 = self._learn_adjacencies(adj_1, node_vec)
        adj_2 = self._learn_adjacencies(adj_2, node_vec)
        
        # flatten
        adj_0 = tf.reshape(adj_0, [-1])
        adj_1 = tf.reshape(adj_1, [-1])
        adj_2 = tf.reshape(adj_2, [-1])

        # forward pass
        adj_0 = tf.matmul(adj_0 * self.w0_1)
        adj_0 = tf.nn.relu(adj_0)
        adj_0 = tf.matmul(adj_0 * self.w0_2)
        adj_0 = tf.nn.relu(adj_0)

        adj_1 = tf.matmul(adj_1 * self.w1_1)
        adj_1 = tf.nn.relu(adj_1)
        adj_1 = tf.matmul(adj_1 * self.w1_2)
        adj_1 = tf.nn.relu(adj_1)

        adj_2 = tf.matmul(adj_2 * self.w2_1)
        adj_2 = tf.nn.relu(adj_2)
        adj_2 = tf.matmul(adj_2 * self.w2_2)
        adj_2 = tf.nn.relu(adj_2) 

        # reshape back to original shape
        adj_0 = tf.reshape(adj_0, shape)
        adj_1 = tf.reshape(adj_1, shape)
        adj_2 = tf.reshape(adj_2, shape)

        return [adj_0, adj_1, adj_2]

    def _learn_adjacencies(self, adj, node_vec):

        '''
            Implements the logic of the Graph Adjacency Layer as follows:

            if adj_ij == 0, new_adj_ij = 0
            if adj_ij == 1, new_adj_ig = |node_vec_i - node_vec_j|
        '''
        # init the output adjacency matrix to zeros
        new_adj = tf.zeros_like(adj, dtype=tf.float32)

        for ik, i in enumerate(adj):
            # iterate columns
            for jk,j in enumerate(i):
                adj_ij = j

                if adj_ij == 0:
                    new_adj[ik,jk] = 0
                
                elif adj_ij == 1:
                    new_adj[ik,jk] = tf.norm(node_vec[ik] - node_vec[jk])
    
        return new_adj

    def compute_output_shape(self, input_shape=[(1, 50, 50), (1, 50, 50), 
                                                (1, 50, 50), (1, 50, 50)]):
        return input_shape[:-1]



class GNN(Layer):

    '''
        Takes two inputs: feature vector of node and the Learned Adjacency 
        Matrix as output by the Adjacency Layer.

        Input:
            n_nodes: The number of 
    '''
    
    def __init__(self, n_features=50, n_nodes=50):
        super(GNN, self).__init__()
        self.n_features = n_features
        self.n_nodes = n_nodes
 

    def build(self, input_shape=None):  # NOTE: input_shape is default arg 
                                        #       which is not used here

        self.w0 = self.add_weight(shape=(self.n_features, self.n_features),
                                    initializer='random_normal',
                                    trainable=True, name='w0')

        self.w1 = self.add_weight(shape=(self.n_features, self.n_features),
                                    initializer='random_normal',
                                    trainable=True, name='w1')

        self.w2 = self.add_weight(shape=(self.n_features, self.n_features),
                                    initializer='random_normal',
                                    trainable=True, name='w2')

    def call(self, inputs):
        

        X, learned_A0, learned_A1, learned_A2 = inputs
        
        product_1 = tf.matmul(tf.matmul(learned_A0, X), self.w0)
        product_2 = tf.matmul(tf.matmul(learned_A1, X), self.w1)
        product_3 = tf.matmul(tf.matmul(learned_A2, X), self.w2)

        X = tf.math.add(tf.math.add(product_1, product_2), product_3)
        X = tf.nn.relu(X)

        return X

    def compute_output_shape(self, input_shape=[(1, 50, 50), (1, 50, 50), 
                                                (1, 50, 50), (1, 50, 50)]):
        return input_shape[0]
        

class GraphOperator(Layer):
    '''
        Layer to generate Adjacency matrices raised to specified power.

        Input:
            power: int, power to raise the input adjacency matrix to such that\
                 a set is generated:
                    A(k) = {A^0, A^1, .., A^power}

        Output:
            A list of adjacency matrices generated as above.
    '''
    def __init__(self, power=2):
        super(GraphOperator, self).__init__()
        self.power = power          # NOTE: not used

    # def build(self,inputShape):
    #     super(GraphOperator, self).build(inputShape)
    #     return

    def call(self, adj):
        
        # TODO: write a function to multiply adj power number of times
        #       
        # adj = adj.numpy
        # power_range = range(0, self.power+1)
        # adj_list = [np.linalg.matrix_power(adj, pow) for pow in power_range]

        assert adj.shape[1] == adj.shape[2], 'Adjacency matrix is not square. \
            Received adjacency matrix with shape {}'.format(adj.shape)
        
        # remove the singleton dimension
        adj = tf.squeeze(adj)

        # get shape of adjacency matrix
        n = adj.shape[0]
        
        # calculate powers of the adjacency matrix
        # NOTE: A^0 = I

        A0 = tf.eye(n)
        A1 = tf.matmul(adj, adj)
        A2 = tf.matmul(A1, adj)
        
        return [A0, A1, A2]

    def compute_output_shape(self, input_shape=(50, 50)):
        return [input_shape, input_shape, input_shape] 
    
 