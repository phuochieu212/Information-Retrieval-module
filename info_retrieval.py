import numpy as np
import scipy.sparse as sp


def remove_stopwords(stopwords, data):
    """Args:
    - stopwords (list): a list of stopwords, each element is a word
    - data (list): a list with each element in it is a string

    Returns:
    - processed_data (list): data has been excluded stopwords
    """

    # Because every element is a long string, we need to split it into words
    # Each element in the orginal data now is a bunch of words
    split_string_data = [element.split() for element in data]

    processed_data = []

    # Proceed every word in new data we have splitted above
    for datapoint in split_string_data:
        new_datapoint = [word for word in datapoint if word not in stopwords]
        processed_data.append(" ".join(new_datapoint.copy()))

    return processed_data


def get_unique_words(data):
    """Args:
    - data (list): a list with each element in it is a string

    Return:
    - unique_words (set): a set of unique words in data
    """

    # Split each string in data into words
    # then add it to a new list. Finally, we converts that list into set
    unique_words = set([word for string in data for word in string.split()])
    return unique_words


def remove_punctuation(
    data,
    punctuations=[
        ".",
        "?",
        "!",
        ",",
        ":",
        ";",
        "'",
        "<",
        ">",
        "(",
        ")",
        "{",
        "}",
        "...",
        '"',
        "[",
        "]",
        "\\",
        "|",
    ],
):
    """Args:
    - data (list): a list with each element in it is a string
    - punctuation_list (list): list of punctuation that you want to eliminate,
    each punctuation is a element in list and in string form.

    If it's not specified, default value will be used:
    ['.', '?', '!', ',', ':', ';', "'", '<', '>', '(', ')',
    '{', '}', '...', '\"', '[', ']', '\\', '|']

    Return:
    - processed_data (list): a list of data with each element is a string
    """

    processed_data = []
    for string in data:
        # Remove punctuation if found in string
        for character in punctuations:
            if character in string:
                string = string.replace(character, "")
        processed_data.append(string)

    return processed_data


def tf(data, dictionary, mtype=int):
    """tf with term t in document d is defined as
    the number of times that t occurs in d.

    Args:
    - data (list): a list with each element in it is a string
    - dictionary (set or list): a list or set that contains unique words
    - mtype (numpy.dtype): matrix type.
    Type of the return value which corresponds to numpy dtype,
    default value is int.

    Return:
    - A 2D matrix with type scipy.sparse.csr_matrix
    """

    row = []
    col = []
    val = []
    # Create a set keeps track of added words
    proceeded_word = set()

    # Iterate all line in dataset
    for index, line in enumerate(data):
        # With each line, split it into words
        for word in line.split():
            if word not in proceeded_word:
                try:
                    dict_index = dictionary.index(word)
                except ValueError:
                    continue
                row.append(index)
                col.append(dict_index)
                val.append(line.count(word))
                proceeded_word.update([word])

        # Clear the exist set as we proceed to the next line
        proceeded_word.clear()

    # Create and return a sparse matrix out of those info
    row = np.array(row)
    col = np.array(col)
    val = np.array(val)

    return sp.csr_matrix((val, (row, col)), (len(data), len(dictionary)), dtype=mtype)


def log_tf(data, dictionary, mtype=float):
    """Logarithm tf with term t in document d is defined as:\n
        tf = 1 + ln(tf)\n
    with ln is the natural logarithm

    Args:
    - data (list): a list with each element in it is a string
    - dictionary (set or list): a list or set that contains unique words
    - mtype (numpy.dtype): matrix type.
    Type of the return value which corresponds to numpy dtype,
    default value is float.

    Return:
    - A 2D matrix with type scipy.sparse.csr_matrix
    """

    tf_var = tf(data, dictionary, mtype=mtype)
    tf_var.data = 1 + np.log(tf_var.data)
    return tf_var


def augmented_tf(data, dictionary, alpha=0.5, mtype=float):
    """Augmented tf with term t in document d is defined as:\n
        tf = alpha + (1-alpha)*tf/max(tf in d)

    Args:
    - data (list): a list with each element in it is a string
    - dictionary (set or list): a list or set that contains unique words
    - alpha (float): floating number with default value is 0.5
    - mtype (numpy.dtype): matrix type.
    Type of the return value which corresponds to numpy dtype,
    default value is float.

    Return:
    - A 2D matrix with type scipy.sparse.csr_matrix
    """

    aug_tf_var = tf(data, dictionary, float)
    aug_tf_var.data *= 1 - alpha

    for i in range(aug_tf_var.shape[0]):
        # Takes non-zero values in row i according to this formula:
        # datapoint i = data[indptr[i]:indptr[i + 1]]
        # Then calculate augmented tf by follow to its definition
        try:
            aug_tf_var.data[aug_tf_var.indptr[i] : aug_tf_var.indptr[i + 1]] /= np.max(
                aug_tf_var.data[aug_tf_var.indptr[i] : aug_tf_var.indptr[i + 1]]
            )
        except ValueError:  # raises if datapoint is empty
            pass

    """
    ______________________________
    The code above is equivalent to this:

    datapoint = aug_tf_var.data[
        aug_tf_var.indptr[i]:aug_tf_var.indptr[i + 1]
        ]
    if datapoint.size == 0:
        continue
    datapoint = datapoint / np.max(datapoint)
    aug_tf_var.data[
        aug_tf_var.indptr[i]:aug_tf_var.indptr[i + 1]
        ] = datapoint
    """

    # Now add the rest
    aug_tf_var.data += alpha

    # For some reasons I dont know why
    # but the method above it's much quicker than this
    # temp = aug_tf_var.max(axis=1)
    # temp.data = 1 / temp.data
    # aug_tf_var = aug_tf_var.multiply(temp) + 0.5

    return sp.csr_matrix(aug_tf_var, dtype=mtype)


def boolean_tf(data, dictionary, mtype=int):
    """Boolean tf with term t in document d is defined as:\n
        if t in d:
            tf = 1
        else: tf = 0

    Args:
    - data (list): a list with each element in it is a string
    - dictionary (set or list): a list or set that contains unique words
    - mtype (numpy.dtype): matrix type.
    Type of the return value which corresponds to numpy dtype,
    default value is int.

    Return:
    - A 2D matrix with type scipy.sparse.csr_matrix
    """

    row = []
    col = []
    val = []
    # Create a set keeps track of added words
    proceeded_word = set()

    # Iterate all line in dataset
    for index, line in enumerate(data):
        # With each line, split it into words
        for word in line.split():
            if word not in proceeded_word:
                try:
                    dict_index = dictionary.index(word)
                except ValueError:
                    continue
                row.append(index)
                col.append(dict_index)
                val.append(1)
                proceeded_word.update([word])
        # Clear the set as we proceed to the next line
        proceeded_word.clear()

    # Create and return a sparse matrix out of those info
    row = np.array(row)
    col = np.array(col)
    val = np.array(val)

    return sp.csr_matrix((val, (row, col)), (len(data), len(dictionary)), dtype=mtype)


def idf(data, dictionary):
    """Adjusted idf will be used to calculate idf according to this formula:\n
        idf = ln(N / (1+[number of data points where the term t appears in]))\n
    with ln is the natural logarithm

    Args:
    - data (list): a list with each element in it is a string
    - dictionary (set or list): a list or set that contains unique words

    Return:
    - A 2D matrix with type scipy.sparse.csr_matrix
    """

    number_of_features = len(dictionary)
    N = len(data)
    matrix = boolean_tf(data, dictionary, float)

    # Convert the csr_matrix to csc_matrix
    matrix_csc = matrix.tocsc()

    # The idea is count how many non-zero values in one feature
    for i in range(number_of_features):
        # Takes non-zero values in col i according to this formula:
        # datapoint i = data[indptr[i]:indptr[i + 1]]
        matrix_csc.data[matrix_csc.indptr[i] : matrix_csc.indptr[i + 1]] = np.log(
            N
            / (
                1
                + np.count_nonzero(
                    matrix_csc.data[matrix_csc.indptr[i] : matrix_csc.indptr[i + 1]]
                )
            )
        )
    """
    ______________________________
    The code above is equivalent to this:

    # Take one feature of data
    feature = matrix_csc.data[matrix_csc.indptr[i]:matrix_csc.indptr[i+1]]

    # Count how many non-zero values in the feature we're looking into
    nonzero_values = np.count_nonzero(feature)

    # Calculate its idf
    feature = np.log(N / (1+nonzero_values))

    # Assign it back to the matrix
    matrix_csc.indptr[i]:matrix_csc.indptr[i+1] = feature
    """

    return matrix_csc.tocsr()


def tf_idf(data, dictionary, func=augmented_tf, alpha=0.5):
    """A faster way and memory efficiency to calculate tf-idf
    instead of taking tf*idf separately.\n
    Augmented tf by default and adjusted idf will be used to calculate.

    Args:
    - data (list): a list with each element in it is a string
    - dictionary (set or list): a list or set that contains unique words
    - func (function name): tf function to calculate tf value.\n
    List of tf function: tf, log_tf, augmented_tf, boolean_tf
    - alpha (float): floating number with default value is 0.5,
    will be used only if func=augmented_tf

    Return:
    - A 2D matrix with type scipy.sparse.csr_matrix
    """

    number_of_features = len(dictionary)
    N = len(data)

    # Calculate tf
    if func == augmented_tf:
        tf_var = func(data, dictionary, alpha=alpha)
    else:
        tf_var = func(data, dictionary, mtype=float)

    # Calulate idf matrix
    # Convert the csr_matrix to csc_matrix
    matrix_csc = tf_var.tocsc()

    # The idea is count how many non-zero values in one feature
    for i in range(number_of_features):
        # Takes non-zero values in col i according to this formula:
        # datapoint i = data[indptr[i]:indptr[i + 1]]
        matrix_csc.data[matrix_csc.indptr[i] : matrix_csc.indptr[i + 1]] = np.log(
            N
            / (
                1
                + np.count_nonzero(
                    matrix_csc.data[matrix_csc.indptr[i] : matrix_csc.indptr[i + 1]]
                )
            )
        )

    """
    ______________________________
    The code above is equivalent to this:

    # Take one feature of data
    feature = matrix_csc.data[matrix_csc.indptr[i]:matrix_csc.indptr[i+1]]

    # Count how many non-zero values in the feature we're looking into
    nonzero_values = np.count_nonzero(feature)

    # Caluclate it idf
    feature = np.log(N / (1+nonzero_values))

    # Assign it back to the matrix
    matrix_csc.indptr[i]:matrix_csc.indptr[i+1] = feature
    """

    # Element-wise tf matrix and idf matrix
    return tf_var.multiply(matrix_csc.tocsr())


def unit_length_scaling(matrix):
    """Scales the components of data point so that
    the completed data point will have Euclidean norm equal to one.\n
    Also, each data point is a row in matrix.

    Args:
    - matrix: a ndarray or a scipy.sparse.csr_matrix type.\n
    If ndarray is passed, it will be converted into scipy.sparse.csr_matrix

    Return:
    - A matrix with type scipy.sparse.csr_matrix
    """

    # Convert matrix to scipy.sparse.csr_matrix with dtype=float
    sparse_matrix = sp.csr_matrix(matrix, dtype=float)

    for i in range(matrix.shape[0]):
        sparse_matrix.data[
            sparse_matrix.indptr[i] : sparse_matrix.indptr[i + 1]
        ] /= np.linalg.norm(
            sparse_matrix.data[sparse_matrix.indptr[i] : sparse_matrix.indptr[i + 1]], 2
        )

    return sparse_matrix


def sim(matrix1, matrix2):
    """
    Calculates the similarity between two vectors.\n
    The formula is: sim(u, v) = cos(u, v) + 1 \n
    If you pass two matrices, the return value will be a vector with each
    element is pairwise similary between matrix2 and matrix1, and so on.\n
    Example:

    \tmatrix1 = [a, b]\n
    \tmatrix2 = [d, e]\n
    The return value will look like this:\n
    \t[[sim(d, a) sim(d, b)]\n
    \t [sim(e, a) sim(e, b)]]\n
    Hope you take the idea.

    Args:
    - matrix1, matrix2: scipy.sparse.csr_matrix type with the same shape.\n
    If ndarray is passed, I don't what could happen.
    So, do it as your own risk.

    Return:
    - A matrix with type numpy.ndarray or scaler if two vectors were passed.
    """

    matrix1 = unit_length_scaling(matrix1)
    matrix2 = unit_length_scaling(matrix2)
    result = matrix2 @ matrix1.T
    result.data = result.data + 1.0
    if result.shape[0] == 1 and result.shape[1] == 1:
        return result.toarray()[0][0]
    else:
        return result.toarray()
