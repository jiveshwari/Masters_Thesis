# -*- coding: utf-8 -*-
"""BERT_fine_tune_git.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1_aA6bCcNMM3OQiJpRS_KLDdAr-JiEDXW

# BERT Fine-tune

#Data Prep
"""

from sklearn.model_selection import train_test_split
import pandas as pd
import json

csv_file = 'url'
df = pd.read_csv(csv_file, delimiter=',')
df = df[df['altlabel_it'].str.lower() != 'none']

neg_file = 'url'
neg_df = pd.read_csv(neg_file, delimiter=',')
neg_df = neg_df[neg_df['altlabel_es'].str.lower() != 'none']

train_df, temp_df = train_test_split(df, test_size=0.4, random_state=42)
val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)

train_data = train_df[['pref_label', 'altlabel_it']].rename(columns={'pref_label': 'source', 'altlabel_it': 'target'}).to_dict(orient='records')
test_data = test_df[['pref_label', 'altlabel_it']].rename(columns={'pref_label': 'source', 'altlabel_it': 'target'}).to_dict(orient='records')

#list to JSON format
json_data = json.dumps(train_data, indent=4, ensure_ascii=False)
with open('train_data.json', 'w', encoding='utf-8') as json_file:
    json_file.write(json_data)

# Function to get a negative example from a different language
def get_negatives_diff_lang(neg_df, positive_example):
    negative_text = random.choice(
        [alt.split(', ')[0] for alt in neg_df['altlabel_es'] if alt.split(', ')[0] != positive_example]
    )
    return negative_text

"""#Model Setup"""

import tensorflow as tf
from transformers import BertTokenizer, TFAutoModel
import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import pandas as pd

# Initialize the tokenizer and model
tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')
model = TFAutoModel.from_pretrained('bert-base-multilingual-cased') #TFautomodel / automodel

#test_df = test_df
test_df_sampled = test_df.sample(n=5, random_state=42) #perplexity must be less than n.

# Extract labels from the sampled DataFrame
source_labels = test_df_sampled['pref_label'].tolist()
target_labels = test_df_sampled['altlabel_it'].tolist()

source_inputs = tokenizer(source_labels, return_tensors='tf', padding=True, truncation=True)
target_inputs = tokenizer(target_labels, return_tensors='tf', padding=True, truncation=True)

# Generate embeddings for labels
source_outputs = model(source_inputs)
source_embeddings = source_outputs.last_hidden_state[:, 0, :].numpy()  # Use the [CLS] token's embeddings
target_outputs = model(target_inputs)
target_embeddings = target_outputs.last_hidden_state[:, 0, :].numpy()  # Use the [CLS] token's embeddings

# Combine embeddings for t-SNE
all_embeddings = np.concatenate((source_embeddings, target_embeddings), axis=0)

# Dimensionality reduction using t-SNE
n_samples = len(source_labels) + len(target_labels)
perplexity = min(2, n_samples - 1)  # Ensure perplexity is less than the number of samples
tsne = TSNE(n_components=2, random_state=0, perplexity=perplexity)
embeddings_2d = tsne.fit_transform(all_embeddings)

"""#Visualize embeddings"""

import plotly.graph_objects as go
from sklearn.manifold import TSNE
import numpy as np
import kaleido

def visualize_embeddings_plotly(embeddings, source_labels, target_labels, title):
    """
    Visualizes embeddings using t-SNE with Plotly, connecting source-target pairs with lines.
    """

      # Perform t-SNE to reduce dimensionality to 2D
    tsne = TSNE(n_components=2, random_state=0, perplexity=2)
    embeddings_2d = tsne.fit_transform(embeddings)


    #Limit to 5 labels for both source and target
    source_labels = source_labels[:10]
    target_labels = target_labels[:10]
    embeddings = embeddings[:20]  # 5 sources + 5 targets

    # Perform t-SNE to reduce dimensionality to 2D
    # tsne = TSNE(n_components=2, random_state=42, perplexity=2, n_iter=500, learning_rate=200)
    # embeddings_2d = tsne.fit_transform(embeddings)

    # Separate source and target embeddings in the 2D space
    num_sources = len(source_labels)
    source_embeddings_2d = embeddings_2d[:num_sources]
    target_embeddings_2d = embeddings_2d[num_sources:]

    # Create a figure for Plotly
    fig = go.Figure()

    # Plot each source-target pair
    for i in range(num_sources):
        # Add a line connecting source and target
        fig.add_trace(go.Scatter(
            x=[source_embeddings_2d[i, 0], target_embeddings_2d[i, 0]],
            y=[source_embeddings_2d[i, 1], target_embeddings_2d[i, 1]],
            mode='lines',
            line=dict(color='gray', width=1),
            showlegend=False
        ))

        # Add source point (circle shape)
        fig.add_trace(go.Scatter(
            x=[source_embeddings_2d[i, 0]],
            y=[source_embeddings_2d[i, 1]],
            mode='markers+text',
            marker=dict(symbol='circle', color='blue', size=15),
            name='Source',
            text=[source_labels[i]],
            textposition='top right',  # Adjusting position
            textfont=dict(size=14, color='blue', family='Arial'),
            showlegend=(i == 0),
        ))

        # Add target point (square shape)
        fig.add_trace(go.Scatter(
            x=[target_embeddings_2d[i, 0]],
            y=[target_embeddings_2d[i, 1]],
            mode='markers+text',
            marker=dict(symbol='square', color='red', size=15),
            name='Target',
            text=[target_labels[i]],
            textposition='bottom left',  # Adjusting position
            textfont=dict(size=14, color='red', family='Arial'),
            showlegend=(i == 0),
        ))

    # Customize layout with additional margin and larger figure size
    fig.update_layout(
        title=title,
        xaxis_title='Dimension 1 (t-SNE)',
        yaxis_title='Dimension 2 (t-SNE)',
        legend_title_text='Label Type',
        xaxis=dict(scaleanchor="y", scaleratio=1),
        yaxis=dict(scaleanchor="x", scaleratio=1),
        margin=dict(l=40, r=40, t=40, b=40),  # Add margins to avoid text cutoffs
        width=1200,  # Increase figure width
        height=400  # Increase figure height
    )

    # Show the figure
    fig.show()

    return fig

"""Before training"""

import numpy as np
import tensorflow as tf

# Ensure eager execution (only necessary if using TensorFlow 1.x)
tf.config.run_functions_eagerly(True)

# Extract initial embeddings
source_outputs = model(source_inputs)
source_embeddings = source_outputs.last_hidden_state[:, 0, :].numpy()
target_outputs = model(target_inputs)
target_embeddings = target_outputs.last_hidden_state[:, 0, :].numpy()

# Combine embeddings for visualization
initial_embeddings = np.concatenate((source_embeddings, target_embeddings), axis=0)

# Visualize initial embeddings with Plotly
fig = visualize_embeddings_plotly(initial_embeddings, source_labels, target_labels, 'Initial BERT Embeddings')


# Save the figure as a PDF
#save_and_download_plot(fig, "/content/altlabel_it_before.pdf")

!pip show kaleido
import kaleido
import plotly.graph_objects as go
from google.colab import files

# Function to save figure as PDF and download it
def save_and_download_plot_as_pdf(fig, file_name):
    # Save the figure as PDF
    img_bytes = fig.to_image(format="pdf")

    # Write the image to a file
    with open(file_name, 'wb') as f:
        f.write(img_bytes)

    # Download the file
    files.download(file_name)

# Example usage
save_and_download_plot_as_pdf(fig, '/content/altlabel_it_before.pdf')

"""#Fine-tuning
dataset is not created.
refer: https://huggingface.co/docs/transformers/en/model_doc/bert

Custom training and Test loop demo
"""

# Improved Testing Loop
def test_model(test_df, threshold=1.0):
    def calculate_distance(embedding1, embedding2):
        return tf.sqrt(tf.reduce_sum(tf.square(embedding1 - embedding2), axis=-1))

    correct_predictions = 0
    total_distance = 0
    distances = []

    for _, row in test_df.iterrows():
        source_text = row['pref_label']
        target_text = row['altlabel_it']

        # Tokenize inputs
        source_input = tokenize(source_text)
        target_input = tokenize(target_text)

        # Compute embeddings
        source_output = bert_model_demo(source_input['input_ids'], attention_mask=source_input['attention_mask']).last_hidden_state[:, 0, :]
        target_output = bert_model_demo(target_input['input_ids'], attention_mask=target_input['attention_mask']).last_hidden_state[:, 0, :]

        # Calculate distance
        distance = calculate_distance(source_output, target_output).numpy()
        total_distance += distance
        distances.append(distance)

        if distance < threshold:
            correct_predictions += 1

    # Calculate accuracy
    accuracy = correct_predictions / len(test_df)
    print(f"Accuracy: {accuracy * 100:.2f}%")

import tensorflow as tf
from transformers import BertTokenizer, TFAutoModel
#from tensorflow.keras.optimizers import Adam
import pandas as pd
import random
from tqdm import tqdm

# Initialize the tokenizer and model
tokenizer_demo = BertTokenizer.from_pretrained('bert-base-multilingual-cased')
bert_model_demo = TFAutoModel.from_pretrained('bert-base-multilingual-cased')

# Define the triplet loss function
def triplet_loss(anchor, positive, negative, margin=5.0):
    # TODO: (1) test sqrt done , (2) increase margin - done wrote a tiny function to check later incase needed.
    # TODO: (1) increase num of training examples - done (2) get positive and negative from other languages (not only german)
    pos_dist = tf.sqrt(tf.reduce_sum(tf.square(anchor - positive), axis=-1))
    neg_dist = tf.sqrt(tf.reduce_sum(tf.square(anchor - negative), axis=-1))
    loss = tf.maximum(pos_dist - neg_dist + margin, 0.0)
    return tf.reduce_mean(loss)

# Tokenize the inputs
def tokenize(text):
    return tokenizer_demo(text, return_tensors='tf', padding=True, truncation=True)

#The warning is due to a future change in the transformers library, where clean_up_tokenization_spaces will default to False.

# Experiment with different margins
def experiment_with_margins(anchor_output, positive_output, negative_output):
    for margin in [0.1, 0.5, 1.0, 2.0, 5.0]:
        loss = triplet_loss(anchor_output, positive_output, negative_output, margin=margin)
        print(f"Margin: {margin}, Loss: {loss.numpy()}")

# Training Loop
def train_model(data, epochs=5, learning_rate=2e-5):
    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    #optimizer = Adam(learning_rate=learning_rate)
    for epoch in range(epochs):
        total_loss = 0
        with tqdm(total=len(data), desc=f"Epoch {epoch + 1}/{epochs}", unit="batch") as pbar:
          for anchor_text, positive_text, negative_text in data:
            with tf.GradientTape() as tape:
                # Tokenize inputs
                anchor_input = tokenize(anchor_text)
                positive_input = tokenize(positive_text)
                negative_input = tokenize(negative_text)

                # Compute embeddings
                anchor_output = bert_model_demo(anchor_input['input_ids'], attention_mask=anchor_input['attention_mask']).last_hidden_state[:, 0, :]
                positive_output = bert_model_demo(positive_input['input_ids'], attention_mask=positive_input['attention_mask']).last_hidden_state[:, 0, :]
                negative_output = bert_model_demo(negative_input['input_ids'], attention_mask=negative_input['attention_mask']).last_hidden_state[:, 0, :]

                # Calculate the triplet loss
                loss = triplet_loss(anchor_output, positive_output, negative_output)
                total_loss += loss

            # Compute gradients and update weights
            gradients = tape.gradient(loss, bert_model_demo.trainable_variables)
            optimizer.apply_gradients(zip(gradients, bert_model_demo.trainable_variables))

            # Update progress bar
            pbar.set_postfix({"loss": total_loss.numpy() / (pbar.n + 1)}) #average loss per batch
            pbar.update(1)

        print(f"Epoch {epoch + 1}, Loss: {total_loss.numpy()}") #total loss for the epoch
        #experiment_with_margins(anchor_output, positive_output, negative_output)

    print("Training complete.")

import logging

sampled_train_df = train_df.sample(n=100, random_state=42)

# Select random indices within the range of the sampled dataframe
train_indices = random.sample(range(len(sampled_train_df)), min(100, len(sampled_train_df)))
training_data = []
print("sampled_train_df Length:", len(sampled_train_df))

# Preparing training triplets with a hard negative sampling strategy
for index in train_indices:
    row = sampled_train_df.iloc[index]
    pref_label = row['pref_label']
    altlabel_es = row['altlabel_es'].split(', ')[0]  # Use the first entry of altlabel as positive
    negative_text = get_negatives_diff_lang(neg_df, altlabel_it)

    training_data.append((pref_label, altlabel_it, negative_text))

print("Training Data:", training_data)  # Check to confirm it's populated
print("training_data Length:", len(training_data))

# Proceed to train the model with the prepared training data
logging.getLogger('tensorflow').setLevel(logging.ERROR) #Supressing this warning - WARNING:tensorflow:Gradients do not exist for variables ['tf_bert_model_1/bert/pooler/dense/kernel:0', 'tf_bert_model_1/bert/pooler/dense/bias:0'] when minimizing the loss. If you're using `model.compile()`, did you forget to provide a `loss` argument?
train_model(training_data)

"""Keep an eye on.

*   Monitoring: Focus on the average loss per batch and the trend over epochs to ensure your model is learning.

*   Expectations: High initial loss values are normal, but the key is a decreasing trend and eventual stabilization.
"""

model.summary()

"""After training"""

import os
from transformers import AutoModelForSeq2SeqLM, NllbTokenizer

# Define the directory and model save path
directory = '/content/drive/MyDrive/Colab Notebooks/Thesis notebooks/Neural-approach/trained_model/it_nl_de_es_fr_zh_full'#'/content/drive/MyDrive/Colab Notebooks/Thesis notebooks/Neural-approach/demo_trained_model/500_demo'
file_name = 'tf_model.h5' #nllb_ft_src_tgt
model_save_path = os.path.join(directory, file_name)

# Ensure the directory exists
os.makedirs(directory, exist_ok=True)

# Save the model and tokenizer
bert_model_demo.save_pretrained(directory)
tokenizer_demo.save_pretrained(directory)

loaded_tokenizer = BertTokenizer.from_pretrained(directory)
loaded_model = TFAutoModel.from_pretrained(directory)
loaded_model.load_weights(model_save_path)

print("Model and tokenizer saved and loaded successfully.")

import numpy as np

# Extract embeddings after training
source_outputs = loaded_model(source_inputs['input_ids'], attention_mask=source_inputs['attention_mask'])
source_embeddings = source_outputs.last_hidden_state[:, 0, :].numpy()
target_outputs = loaded_model(target_inputs['input_ids'], attention_mask=target_inputs['attention_mask'])
target_embeddings = target_outputs.last_hidden_state[:, 0, :].numpy()

# Combine embeddings for visualization
final_embeddings = np.concatenate((source_embeddings, target_embeddings), axis=0)

# Visualize final embeddings with Plotly
fig2 = visualize_embeddings_plotly(final_embeddings, source_labels, target_labels, 'Final BERT Embeddings')

save_and_download_plot_as_pdf(fig2, '/content/altlabel_it_after.pdf')