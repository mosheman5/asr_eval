import random

import streamlit as st
import json
import zipfile
from pathlib import Path

st.title('ASR Model Evaluation')

# Upload JSON file
json_file = st.file_uploader('Upload JSON file with transcriptions', type='json')

# Upload ZIP file
zip_file = st.file_uploader('Upload ZIP file with audio files', type='zip')

if json_file and zip_file:

    # Load transcriptions
    @st.cache_data
    def load_transcriptions(json_file):
        transcriptions = json.load(json_file)
        return transcriptions

    # Load audio files
    @st.cache_data
    def load_audio_files(zip_file):
        audio_files = {}
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith('.wav'):
                    data = zip_ref.read(file)
                    audio_files[Path(file).name] = data
        return audio_files

    transcriptions = load_transcriptions(json_file)
    audio_files = load_audio_files(zip_file)
    num_sentences = len(transcriptions['large-v2'])
    all_keys = list(transcriptions['large-v2'].keys())

    # Initialize session state variables
    if 'sentence_index' not in st.session_state:
        st.session_state.sentence_index = 0
    if 'rankings' not in st.session_state:
        st.session_state.rankings = [{} for _ in range(num_sentences)]
    if 'model_mappings' not in st.session_state:
        st.session_state.model_mappings = [{} for _ in range(num_sentences)]

    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button('Previous'):
            if st.session_state.sentence_index > 0:
                st.session_state.sentence_index -= 1
    with col3:
        if st.button('Next'):
            if st.session_state.sentence_index < num_sentences - 1:
                st.session_state.sentence_index += 1
    with col2:
        st.write(f'Sentence {st.session_state.sentence_index + 1} of {num_sentences}')

    # Get current sentence data
    idx = st.session_state.sentence_index
    key = all_keys[idx]
    current_transcriptions = {model: d[key] for model, d in transcriptions.items()}
    audio_data = audio_files[key]

    # Play audio
    st.audio(audio_data, format='audio/wav')

    # Display transcriptions and collect rankings
    rankings = st.session_state.rankings[idx]

    model_mapping = st.session_state.model_mappings[idx]

    # Generate fake model names and shuffle them
    if not model_mapping:
        fake_names = [f'System {i+1}' for i in range(len(current_transcriptions))]
        real_model_names = list(current_transcriptions.keys())
        random.shuffle(real_model_names)
        model_mapping = dict(zip(fake_names, real_model_names))
        st.session_state.model_mappings[idx] = model_mapping

    st.write("### Transcriptions and Rankings")
    for fake_model_name in model_mapping.keys():
        real_model_name = model_mapping[fake_model_name]
        st.write(f"**Model**: {fake_model_name }")
        st.write(f"**Transcription**: {current_transcriptions[real_model_name]}")
        ranking_options = [1, 2, 3, 4, 5]
        default_index = rankings.get(fake_model_name, 1) - 1  # Adjust for zero-based index
        ranking = st.radio(
            f'Rank for {fake_model_name}',
            options=ranking_options,
            index=default_index,
            key=f'{idx}_{fake_model_name}',
            horizontal=True,
        )
        rankings[fake_model_name] = ranking
        rankings[real_model_name] = ranking
    rankings['audio'] = key
    rankings['mapping'] = model_mapping

    # Option to save rankings
    if st.button('Save Rankings'):
        rankings_json = json.dumps(st.session_state.rankings, indent=2)
        st.download_button(
            label='Download Rankings',
            data=rankings_json,
            file_name='rankings.json',
            mime='application/json'
        )
        st.success('Rankings are ready for download!')

    st.write("#### Note: The order of the models has been randomized, eg, model 'system 1' may not correspond to the same model across sentences.")

else:
    st.warning('Please upload both the JSON and ZIP files to proceed.')
