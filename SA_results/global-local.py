import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Use scientific style for the plot
plt.style.use('seaborn-whitegrid')

# Read the Excel file as a DataFrame, use the header=6 to locate the column names
df = pd.read_excel('OAT-global-local-table.xlsx', header=6)

# Extract specific columns
furthest_allowed = df['furthest-allowed']
ticks = df['ticks']
distance_traveled = df['distance-traveled of robots']

# For each value of bot-speed-ratio, calculate how many of them have value of ticks smaller than 10000
filtered_df = df[df['ticks'] < 10000]
filtered_counts = filtered_df['furthest-allowed'].value_counts()

# Calculate the total counts of each 'furthest-allowed' value
total_counts = df['furthest-allowed'].value_counts()
ratio = filtered_counts / total_counts
ratio = ratio.fillna(0)

grouped = filtered_df.groupby(
    'furthest-allowed')['distance-traveled of robots']
mean_distance = grouped.mean()
std_distance = grouped.std()

grouped_ticks = df.groupby('furthest-allowed')['ticks']
mean_ticks = grouped_ticks.mean()
std_ticks = grouped_ticks.std()

# Create a figure and a set of subplots
fig, axs = plt.subplots(3, 1)
plt.subplots_adjust(hspace=0.3)

# draw scatter plots for the success rate
axs[0].scatter(ratio.index, ratio)
axs[0].set_xlabel('furthest-allowed', fontsize=12)
axs[0].set_ylabel('Success rate', fontsize=12)
axs[0].set_xticks(np.arange(min(ratio.index), max(ratio.index)+5, 5))

axs[1].errorbar(mean_distance.index, mean_distance,
                yerr=std_distance, fmt='o', capsize=6)
axs[1].set_xlabel('furthest-allowed', fontsize=12)
axs[1].set_ylabel('Distance Traveled', fontsize=12)
xticks_a = axs[0].get_xticks()
axs[1].set_xticks(xticks_a)

axs[2].errorbar(mean_ticks.index, mean_ticks,
                yerr=std_ticks, fmt='o', capsize=6)
axs[2].set_xlabel('furthest-allowed', fontsize=12)
axs[2].set_ylabel('Ticks', fontsize=12)
axs[2].set_xticks(xticks_a)

axs[0].text(-0.12, 1, 'a', transform=axs[0].transAxes,
            size=20, weight='bold')
axs[1].text(-0.12, 1, 'b', transform=axs[1].transAxes,
            size=20, weight='bold')
axs[2].text(-0.12, 1, 'c', transform=axs[2].transAxes,
            size=20, weight='bold')

# Display the plot
plt.show()
