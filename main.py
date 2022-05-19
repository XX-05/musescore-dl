import jmuse


if __name__ == "__main__":
    score = jmuse.search_scores("four out of five")[0]
    print(f"downloading {score.title}")
    score.download()
    score.download_mp3()
