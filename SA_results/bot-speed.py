import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Use scientific style for the plot
plt.style.use('seaborn-whitegrid')

# Read the Excel file as a DataFrame, use the header=6 to locate the column names
df = pd.read_excel('OAT-bot-speed-table.xlsx', header=6)
df_finer = pd.read_excel('OAT-bot-speed-table-finer.xlsx', header=6)

# Extract specific columns
bot_speed_ratio = df['bot-speed-ratio']
ticks = df['ticks']
distance_traveled = df['distance-traveled of robots']
bot_speed_ratio_finer = df_finer['bot-speed-ratio']
ticks_finer = df_finer['ticks']
distance_traveled_finer = df_finer['distance-traveled of robots']

# For each value of bot-speed-ratio, calculate how many of them have value of ticks smaller than 10000
filtered_df = df[df['ticks'] < 10000]
filtered_counts = filtered_df['bot-speed-ratio'].value_counts()
filtered_df_finer = df_finer[df_finer['ticks'] < 10000]
filtered_counts_finer = filtered_df_finer['bot-speed-ratio'].value_counts()

# Calculate the total counts of each 'bot-speed-ratio' value
total_counts = df['bot-speed-ratio'].value_counts()
ratio = filtered_counts / total_counts
ratio = ratio.fillna(0)

total_counts_finer = df_finer['bot-speed-ratio'].value_counts()
ratio_finer = filtered_counts_finer / total_counts_finer
ratio_finer = ratio_finer.fillna(0)

# Group by 'bot-speed-ratio' and calculate the mean and standard deviation of 'distance-traveled of robots'
grouped_test = filtered_df.groupby('bot-speed-ratio')
print(grouped_test.first())
grouped = filtered_df.groupby('bot-speed-ratio')['distance-traveled of robots']
mean_distance = grouped.mean()
std_distance = grouped.std()

grouped_finer = filtered_df_finer.groupby(
    'bot-speed-ratio')['distance-traveled of robots']
mean_distance_finer = grouped_finer.mean()
std_distance_finer = grouped_finer.std()

# group by 'bot-speed-ratio' and calculate the mean and standard deviation of 'ticks'
grouped_ticks = df.groupby('bot-speed-ratio')['ticks']
mean_ticks = grouped_ticks.mean()
std_ticks = grouped_ticks.std()

grouped_ticks_finer = df_finer.groupby('bot-speed-ratio')['ticks']
mean_ticks_finer = grouped_ticks_finer.mean()
std_ticks_finer = grouped_ticks_finer.std()

# Create a figure and a set of subplots
fig, axs = plt.subplots(3, 2)
plt.subplots_adjust(hspace=0.3)

# draw scatter plots for the success rate
axs[0, 0].scatter(ratio.index, ratio)
axs[0, 0].set_xlabel('bot-speed-ratio', fontsize=12)
axs[0, 0].set_ylabel('Success rate', fontsize=12)
# Set the x-axis grid interval to 1
axs[0, 0].set_xticks(np.arange(min(ratio.index), max(ratio.index)+1, 1))


axs[0, 1].scatter(ratio_finer.index, ratio_finer)
axs[0, 1].set_xlabel('bot-speed-ratio', fontsize=12)
axs[0, 1].set_ylabel('Success rate', fontsize=12)
axs[0, 1].set_xticks(np.arange(min(ratio_finer.index),
                     max(ratio_finer.index)+0.1, 0.1))

# Draw distance traveled plots with error bars
axs[1, 0].errorbar(mean_distance.index, mean_distance,
                   yerr=std_distance, fmt='o', capsize=6)

# Set the labels for the x and y axes
axs[1, 0].set_xlabel('bot-speed-ratio', fontsize=12)
axs[1, 0].set_ylabel('Distance Traveled', fontsize=12)
xticks_a = axs[0, 0].get_xticks()
axs[1, 0].set_xticks(xticks_a)
xlim_a = axs[0, 0].get_xlim()
axs[1, 0].set_xlim(xlim_a)


axs[1, 1].errorbar(mean_distance_finer.index, mean_distance_finer,
                   yerr=std_distance_finer, fmt='o', capsize=6)
axs[1, 1].set_xlabel('bot-speed-ratio', fontsize=12)
axs[1, 1].set_ylabel('Distance Traveled', fontsize=12)
xticks_b = axs[0, 1].get_xticks()
axs[1, 1].set_xticks(xticks_b)
xlim_b = axs[0, 1].get_xlim()
axs[1, 1].set_xlim(xlim_b)

axs[2, 0].errorbar(mean_ticks.index, mean_ticks,
                   yerr=std_ticks, fmt='o', capsize=6)
axs[2, 0].set_xlabel('bot-speed-ratio', fontsize=12)
axs[2, 0].set_ylabel('Ticks', fontsize=12)
axs[2, 0].set_xticks(xticks_a)
axs[2, 0].set_xlim(xlim_a)

axs[2, 1].errorbar(mean_ticks_finer.index, mean_ticks_finer,
                   yerr=std_ticks_finer, fmt='o', capsize=6)
axs[2, 1].set_xlabel('bot-speed-ratio', fontsize=12)
axs[2, 1].set_ylabel('Ticks', fontsize=12)
axs[2, 1].set_xticks(xticks_b)
axs[2, 1].set_xlim(xlim_b)
# Add a marker to the first subplot
axs[0, 0].text(-0.12, 1, 'a', transform=axs[0, 0].transAxes,
               size=20, weight='bold')

# Add a marker to the second subplot
axs[0, 1].text(-0.12, 1, 'b', transform=axs[0, 1].transAxes,
               size=20, weight='bold')

# Add a marker to the third subplot
axs[1, 0].text(-0.12, 1, 'c', transform=axs[1, 0].transAxes,
               size=20, weight='bold')

# Add a marker to the fourth subplot
axs[1, 1].text(-0.12, 1, 'd', transform=axs[1, 1].transAxes,
               size=20, weight='bold')

axs[2, 0].text(-0.12, 1, 'e', transform=axs[2, 0].transAxes,
               size=20, weight='bold')

axs[2, 1].text(-0.12, 1, 'f', transform=axs[2, 1].transAxes,
               size=20, weight='bold')

# Display the plot
plt.show()
