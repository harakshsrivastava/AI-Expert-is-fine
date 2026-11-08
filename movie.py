
"""AI Movie Recommendation System 2.0

Install: pip install pandas scikit-learn textblob colorama
Place imdb_top_1000.csv beside this script, then run with Python 3.
"""
from pathlib import Path
import random
import time
import textwrap

import pandas as pd
from colorama import Fore, Style, init
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob

init(autoreset=True)
DATASET = Path(__file__).resolve().parent / 'imdb_top_1000.csv'
REQUIRED = {'Series_Title', 'Genre', 'Overview', 'IMDB_Rating'}


def load_movies():
    try:
        movies = pd.read_csv(DATASET)
    except FileNotFoundError:
        raise SystemExit(Fore.RED + f'Missing dataset: {DATASET}\nDownload imdb_top_1000.csv and place it next to this script.')
    missing = REQUIRED - set(movies.columns)
    if missing:
        raise SystemExit(Fore.RED + f'Dataset missing columns: {", ".join(sorted(missing))}')
    movies = movies.copy()
    movies['IMDB_Rating'] = pd.to_numeric(movies['IMDB_Rating'], errors='coerce')
    movies = movies.dropna(subset=['Series_Title', 'IMDB_Rating'])
    movies['Genre'] = movies['Genre'].fillna('').astype(str)
    movies['Overview'] = movies['Overview'].fillna('').astype(str)
    movies = movies.drop_duplicates(subset=['Series_Title']).reset_index(drop=True)
    if movies.empty:
        raise SystemExit(Fore.RED + 'The dataset contains no valid movies.')
    movies['polarity'] = movies['Overview'].map(lambda s: TextBlob(s).sentiment.polarity)
    # Build TF-IDF features once, rather than recomputing for each request.
    movies['features'] = movies['Genre'].str.replace(',', ' ', regex=False) + ' ' + movies['Overview']
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(movies['features'])
    genres = sorted({g.strip() for entry in movies['Genre'] for g in entry.split(',') if g.strip()})
    return movies, vectorizer, matrix, genres


def sentiment_label(score):
    if score > 0.05:
        return 'Positive 😊'
    if score < -0.05:
        return 'Negative 😞'
    return 'Neutral 😐'


def ask_choice(prompt, choices):
    while True:
        value = input(Fore.YELLOW + prompt).strip().lower()
        if value in choices:
            return value
        print(Fore.RED + 'Invalid choice. Try again.')


def ask_genre(genres):
    print(Fore.GREEN + '\nAvailable genres:')
    print(Fore.CYAN + '0. Any genre')
    for number, genre in enumerate(genres, 1):
        print(Fore.CYAN + f'{number}. {genre}')
    while True:
        answer = input(Fore.YELLOW + 'Choose a genre number or name: ').strip()
        if answer.lower() in {'0', 'any', 'skip'}:
            return None
        if answer.isdigit() and 1 <= int(answer) <= len(genres):
            return genres[int(answer) - 1]
        for genre in genres:
            if answer.casefold() == genre.casefold():
                return genre
        print(Fore.RED + 'Please choose a listed genre.')


def ask_rating(movies):
    low, high = float(movies['IMDB_Rating'].min()), float(movies['IMDB_Rating'].max())
    while True:
        answer = input(Fore.YELLOW + f'Minimum IMDb rating ({low:.1f}–{high:.1f}, or skip): ').strip().lower()
        if answer in {'', 'skip'}:
            return None
        try:
            rating = float(answer)
            if low <= rating <= high:
                return rating
        except ValueError:
            pass
        print(Fore.RED + 'Enter a valid rating in the displayed range, or skip.')


def recommend(movies, vectorizer, matrix, mode, genre, mood, rating, themes, seen, count=5):
    candidates = movies
    if genre:
        candidates = candidates[candidates['Genre'].map(lambda text: genre.casefold() in [g.strip().casefold() for g in text.split(',')])]
    if rating is not None:
        candidates = candidates[candidates['IMDB_Rating'] >= rating]
    if candidates.empty:
        return [], False
    unseen = candidates[~candidates.index.isin(seen)]
    restarted = unseen.empty
    if restarted:
        seen.clear()
        unseen = candidates
    if mode == 'random':
        chosen = unseen.sample(n=min(count, len(unseen)))
    else:
        # Similarity uses movie descriptions and genre, not just random sampling.
        # Mood and themes become query text. Polarity is a small secondary signal.
        query = ' '.join(part for part in [genre or '', mood, themes] if part).strip()
        if query:
            query_vector = vectorizer.transform([query])
            scores = cosine_similarity(query_vector, matrix[unseen.index]).ravel()
        else:
            scores = [0.0] * len(unseen)
        target_polarity = TextBlob(mood).sentiment.polarity if mood else 0.0
        scored = unseen.copy()
        scored['match_score'] = scores
        if mood:
            scored['match_score'] += 0.10 * (1 - (scored['polarity'] - target_polarity).abs() / 2)
        # A small rating tie-breaker rewards quality when similarity is close.
        scored['match_score'] += 0.01 * scored['IMDB_Rating'] / 10
        chosen = scored.sort_values(['match_score', 'IMDB_Rating'], ascending=False).head(count)
    seen.update(int(i) for i in chosen.index)
    return [row for _, row in chosen.iterrows()], restarted


def display(recommendations, name, mode):
    print(Fore.YELLOW + f'\n🍿 {mode.title()} Movie Recommendations for {name}:\n')
    if not recommendations:
        print(Fore.RED + 'No suitable movies found. Try a different genre or lower rating.')
        return
    for number, movie in enumerate(recommendations, 1):
        print(Fore.CYAN + f'{number}. 🎥 {movie["Series_Title"]}')
        print(f'   Genres: {movie["Genre"] or "Unknown"}')
        print(f'   IMDb rating: {movie["IMDB_Rating"]:.1f}/10')
        print(f'   Overview: {textwrap.fill(movie["Overview"] or "No overview available.", width=85, subsequent_indent="      ")}')
        print(f'   Overview sentiment: {sentiment_label(movie["polarity"])} (polarity {movie["polarity"]:+.2f})')
        print()


def main():
    movies, vectorizer, matrix, genres = load_movies()
    print(Fore.BLUE + '🎥 Welcome to your Personal Movie Recommendation Assistant! 🎥')
    name = input(Fore.YELLOW + "What's your name? ").strip() or 'Movie Fan'
    print(Fore.GREEN + f'\nGreat to meet you, {name}!')
    seen = set()
    while True:
        print(Fore.BLUE + '\nChoose a recommendation mode:')
        print('1. AI-based recommendation (TF-IDF + cosine similarity)')
        print('2. Random recommendation')
        print('3. Exit')
        option = ask_choice('Enter 1, 2, or 3: ', {'1', '2', '3'})
        if option == '3':
            break
        mode = 'ai' if option == '1' else 'random'
        genre = ask_genre(genres)
        mood = input(Fore.YELLOW + 'How are you feeling today? (optional): ').strip()
        if mood:
            polarity = TextBlob(mood).sentiment.polarity
            print(Fore.GREEN + f'Your mood: {sentiment_label(polarity)} ({polarity:+.2f})')
        rating = ask_rating(movies)
        themes = input(Fore.YELLOW + 'Movie themes or keywords (optional): ').strip() if mode == 'ai' else ''
        seen.clear()
        while True:
            print(Fore.BLUE + '\nFinding movies', end='', flush=True)
            for _ in range(3):
                print('.', end='', flush=True)
                time.sleep(0.2)
            print()
            results, restarted = recommend(movies, vectorizer, matrix, mode, genre, mood, rating, themes, seen)
            if restarted and results:
                print(Fore.YELLOW + 'All matching movies were shown; starting the list again.')
            display(results, name, mode)
            if not results:
                break
            action = ask_choice('More movies (m), change preferences (c), or quit (q)? ', {'m', 'c', 'q'})
            if action == 'm':
                continue
            if action == 'q':
                print(Fore.GREEN + f'\nEnjoy your movie picks, {name}! 🎬🍿')
                return
            break
    print(Fore.GREEN + f'\nEnjoy your movie picks, {name}! 🎬🍿')


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('\nGoodbye!')
