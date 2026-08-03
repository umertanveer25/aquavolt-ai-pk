from PIL import Image

# Load the combined image
img_path = r"C:\Users\umert\.gemini\antigravity\brain\8d23e27f-337c-4bdb-abe2-28bd05fbe957\media__1784430594345.jpg"
img = Image.open(img_path)

width, height = img.size

# The image has a horizontal line separating the top and bottom. 
# It looks exactly 50/50 split, maybe slightly different, but cutting exactly in half should work well.
# Let's crop it at height // 2.
mid = int(height * 0.535) # Looking at the image, the separator line is slightly below center. Let's do 53.5%.

top_half = img.crop((0, 0, width, mid))
bottom_half = img.crop((0, mid, width, height))

# Save to figures directory
top_path = r"C:\Users\umert\aquavolt-ai-pk\papers\paper_edge_effects\figures\fig1_spatial_heatmaps.jpg"
bottom_path = r"C:\Users\umert\aquavolt-ai-pk\papers\paper_edge_effects\figures\fig10_irrigation_penalty.jpg"

top_half.save(top_path, quality=95)
bottom_half.save(bottom_path, quality=95)

print("Image sliced successfully!")
