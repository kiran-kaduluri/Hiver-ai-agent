import pandas as pd
from tqdm import tqdm

def extract_amazon_pairs(
    raw_csv_path: str = "data/raw/twcs.csv", 
    output_csv_path: str = "data/processed/amazon_pairs.csv", 
    target_pairs: int = 5000
):
    print("Step 1: Loading raw tweet dataset...")
    # Essential columns matrame load chestunnam RAM save cheyadaniki
    usecols = ["tweet_id", "author_id", "in_response_to_tweet_id", "text", "inbound"]
    
    # Dataset peddhadhi kabatti chunks lo chaduvutunnam
    print("Step 2: Filtering AmazonHelp interactions...")
    chunks = pd.read_csv(raw_csv_path, usecols=usecols, chunksize=100000, low_memory=False)
    
    amazon_tweets = []
    for chunk in tqdm(chunks, desc="Reading chunks"):
        # AmazonHelp pampina tweets leda inbound tweets ni select chestunnam
        mask = (chunk["author_id"] == "AmazonHelp") | (chunk["text"].str.contains("@AmazonHelp", case=False, na=False))
        amazon_tweets.append(chunk[mask])
        
    df_amazon = pd.concat(amazon_tweets, ignore_index=True)
    print(f"Total Amazon-related tweets filtered: {len(df_amazon)}")

    # Fast lookup kosam dictionary map create chestunnam
    print("Step 3: Pairing customer inquiries with AmazonHelp replies...")
    tweet_dict = df_amazon.set_index("tweet_id").to_dict(orient="index")

    # Amazon replies ni filter cheyandi
    brand_replies = df_amazon[df_amazon["author_id"] == "AmazonHelp"].dropna(subset=["in_response_to_tweet_id"])

    pairs = []
    for _, reply_row in tqdm(brand_replies.iterrows(), total=len(brand_replies), desc="Building pairs"):
        parent_id = reply_row["in_response_to_tweet_id"]
        
        # Parent ID mana records lo unte, adi customer tweet ah kaadha check chestham
        if parent_id in tweet_dict:
            parent_tweet = tweet_dict[parent_id]
            if parent_tweet["author_id"] != "AmazonHelp":
                pairs.append({
                    "customer_tweet_id": parent_id,
                    "customer_text": str(parent_tweet["text"]).strip(),
                    "brand_reply_id": reply_row["tweet_id"],
                    "brand_reply_text": str(reply_row["text"]).strip()
                })
                
        if len(pairs) >= target_pairs:
            break

    pairs_df = pd.DataFrame(pairs)
    pairs_df.to_csv(output_csv_path, index=False)
    print(f"\nSuccess! Saved {len(pairs_df)} cleaned pairs to '{output_csv_path}'.")

if __name__ == "__main__":
    extract_amazon_pairs()