import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Use scientific style for the plot
plt.style.use('seaborn-whitegrid')

# Read the Excel file as a DataFrame, use the header=6 to locate the column names
df = pd.read_excel('bot-speed-global-local-table.xlsx', header=6)
df_finer = pd.read_excel('bot-speed-finer-global-local-table.xlsx', header=6)
df_global = df[df['global-vision'] == True]
df_local = df[df['global-vision'] == False]
df_global_finer = df_finer[df_finer['global-vision'] == True]
df_local_finer = df_finer[df_finer['global-vision'] == False]

# Extract specific columns
bot_speed_ratio_global = df_global['bot-speed-ratio']
bot_speed_ratio_local = df_local['bot-speed-ratio']
bot_speed_ratio_global_finer = df_global_finer['bot-speed-ratio']
bot_speed_ratio_local_finer = df_local_finer['bot-speed-ratio']
ticks_global = df_global['ticks']
ticks_local = df_local['ticks']
ticks_global_finer = df_global_finer['ticks']
ticks_local_finer = df_local_finer['ticks']
distance_traveled_global = df_global['distance-traveled of robots']
distance_traveled_local = df_local['distance-traveled of robots']
distance_traveled_global_finer = df_global_finer['distance-traveled of robots']
distance_traveled_local_finer = df_local_finer['distance-traveled of robots']

# For each value of bot-speed-ratio, calculate how many of them have value of ticks smaller than 10000
filtered_df_global = df_global[df_global['ticks'] < 10000]
filtered_counts_global = filtered_df_global['bot-speed-ratio'].value_counts()
filtered_df_local = df_local[df_local['ticks'] < 10000]
filtered_counts_local = filtered_df_local['bot-speed-ratio'].value_counts()
filtered_df_global_finer = df_global_finer[df_global_finer['ticks'] < 10000]
filtered_counts_global_finer = filtered_df_global_finer['bot-speed-ratio'].value_counts(
)
filtered_df_local_finer = df_local_finer[df_local_finer['ticks'] < 10000]
filtered_counts_local_finer = filtered_df_local_finer['bot-speed-ratio'].value_counts(
)

# Calculate the total counts of each 'bot-speed-ratio' value
total_counts_global = df_global['bot-speed-ratio'].value_counts()
total_counts_local = df_local['bot-speed-ratio'].value_counts()
total_counts_global_finer = df_global_finer['bot-speed-ratio'].value_counts()
total_counts_local_finer = df_local_finer['bot-speed-ratio'].value_counts()
ratio_global = filtered_counts_global / total_counts_global
ratio_global = ratio_global.fillna(0)
ratio_local = filtered_counts_local / total_counts_local
ratio_local = ratio_local.fillna(0)
ratio_global_finer = filtered_counts_global_finer / total_counts_global_finer
ratio_global_finer = ratio_global_finer.fillna(0)
ratio_local_finer = filtered_counts_local_finer / total_counts_local_finer
ratio_local_finer = ratio_local_finer.fillna(0)

# Group by 'bot-speed-ratio' and calculate the mean and standard deviation of 'distance-traveled of robots'
grouped_global_distance = filtered_df_global.groupby(
    'bot-speed-ratio')['distance-traveled of robots']
mean_distance_global = grouped_global_distance.mean()
std_distance_global = grouped_global_distance.std()
grouped_local_distance = filtered_df_local.groupby(
    'bot-speed-ratio')['distance-traveled of robots']
mean_distance_local = grouped_local_distance.mean()
std_distance_local = grouped_local_distance.std()

grouped_global_distance_finer = filtered_df_global_finer.groupby(
    'bot-speed-ratio')['distance-traveled of robots']
mean_distance_global_finer = grouped_global_distance_finer.mean()
std_distance_global_finer = grouped_global_distance_finer.std()
grouped_local_distance_finer = filtered_df_local_finer.groupby(
    'bot-speed-ratio')['distance-traveled of robots']
mean_distance_local_finer = grouped_local_distance_finer.mean()
std_distance_local_finer = grouped_local_distance_finer.std()

# Group by 'bot-speed-ratio' and calculate the mean and standard deviation of 'ticks'
grouped_global_ticks = df_global.groupby('bot-speed-ratio')['ticks']
mean_ticks = grouped_global_ticks.mean()
std_ticks = grouped_global_ticks.std()
grouped_local_ticks = df_local.groupby('bot-speed-ratio')['ticks']
mean_ticks_local = grouped_local_ticks.mean()
std_ticks_local = grouped_local_ticks.std()

grouped_global_ticks_finer = df_global_finer.groupby(
    'bot-speed-ratio')['ticks']
mean_ticks_finer = grouped_global_ticks_finer.mean()
std_ticks_finer = grouped_global_ticks_finer.std()
grouped_local_ticks_finer = df_local_finer.groupby('bot-speed-ratio')['ticks']
mean_ticks_local_finer = grouped_local_ticks_finer.mean()
std_ticks_local_finer = grouped_local_ticks_finer.std()

# Create a figure and a set of subplots
fig, axs = plt.subplots(3, 2, sharex='col', sharey='row')
# fig, axs = plt.subplots(3, 2)
plt.subplots_adjust(hspace=0.3)

# draw plots for the success rate
axs[0, 0].plot(ratio_global.index, ratio_global, 'o:', label='Global Vision')
axs[0, 0].plot(ratio_local.index, ratio_local, 'o-', label='Local Vision')
# axs[0, 0].set_xlabel('bot-speed-ratio', fontsize=12)
axs[0, 0].set_ylabel('Success Rate', fontsize=12)
axs[0, 0].set_xticks(np.arange(min(ratio_global.index),
                               max(ratio_global.index)+1, 1))


axs[0, 1].plot(ratio_global_finer.index, ratio_global_finer,
               'o:', label='Global Vision')
axs[0, 1].plot(ratio_local_finer.index, ratio_local_finer,
               'o-', label='Local Vision')
# axs[0, 1].set_xlabel('bot-speed-ratio', fontsize=12)
# axs[0, 1].set_ylabel('Success Rate', fontsize=12)
axs[0, 1].set_xticks(np.arange(min(ratio_global_finer.index),
                               max(ratio_global_finer.index)+0.1, 0.1))


# draw plots for the distance traveled
axs[1, 0].errorbar(mean_distance_global.index, mean_distance_global,
                   yerr=std_distance_global, fmt='o:', capsize=6, label='Global Vision')
axs[1, 0].errorbar(mean_distance_local.index, mean_distance_local,
                   yerr=std_distance_local, fmt='o-', capsize=6, label='Local Vision')
# axs[1, 0].set_xlabel('bot-speed-ratio', fontsize=12)
axs[1, 0].set_ylabel('Distance Traveled', fontsize=12)
xticks_a = axs[0, 0].get_xticks()
xlim_a = axs[0, 0].get_xlim()
axs[1, 0].set_xticks(xticks_a)
axs[1, 0].set_xlim(xlim_a)


axs[1, 1].errorbar(mean_distance_global_finer.index, mean_distance_global_finer,
                   yerr=std_distance_global_finer, fmt='o:', capsize=6, label='Global Vision')
axs[1, 1].errorbar(mean_distance_local_finer.index, mean_distance_local_finer,
                   yerr=std_distance_local_finer, fmt='o-', capsize=6, label='Local Vision')
# axs[1, 1].set_xlabel('bot-speed-ratio', fontsize=12)
# axs[1, 1].set_ylabel('Distance Traveled', fontsize=12)
xticks_b = axs[0, 1].get_xticks()
xlim_b = axs[0, 1].get_xlim()
axs[1, 1].set_xlim(xlim_b)
axs[1, 1].set_xticks(xticks_b)


# draw plots for the ticks
axs[2, 0].errorbar(mean_ticks.index, mean_ticks,
                   yerr=std_ticks, fmt='o:', capsize=6, label='Global Vision')
axs[2, 0].errorbar(mean_ticks_local.index, mean_ticks_local,
                   yerr=std_ticks_local, fmt='o-', capsize=6, label='Local Vision')
axs[2, 0].set_xlabel('bot-speed-ratio', fontsize=12)
axs[2, 0].set_ylabel('Time to Finish', fontsize=12)
axs[2, 0].set_xticks(xticks_a)
axs[2, 0].set_xlim(xlim_a)


axs[2, 1].errorbar(mean_ticks_finer.index, mean_ticks_finer,
                   yerr=std_ticks_finer, fmt='o:', capsize=6, label='Global Vision')
axs[2, 1].errorbar(mean_ticks_local_finer.index, mean_ticks_local_finer,
                   yerr=std_ticks_local_finer, fmt='o-', capsize=6, label='Local Vision')
axs[2, 1].set_xlabel('bot-speed-ratio', fontsize=12)
# axs[2, 1].set_ylabel('Time to Finish', fontsize=12)
axs[2, 1].set_xticks(xticks_b)
axs[2, 1].set_xlim(xlim_b)


# Add a marker to the first subplot
axs[0, 0].text(-0.12, 1, 'a1', transform=axs[0, 0].transAxes,
               size=20, weight='bold')

# Add a marker to the second subplot
axs[0, 1].text(-0.12, 1, 'b1', transform=axs[0, 1].transAxes,
               size=20, weight='bold')

# Add a marker to the third subplot
axs[1, 0].text(-0.12, 1, 'a2', transform=axs[1, 0].transAxes,
               size=20, weight='bold')

# Add a marker to the fourth subplot
axs[1, 1].text(-0.12, 1, 'b2', transform=axs[1, 1].transAxes,
               size=20, weight='bold')

axs[2, 0].text(-0.12, 1, 'a3', transform=axs[2, 0].transAxes,
               size=20, weight='bold')

axs[2, 1].text(-0.12, 1, 'b3', transform=axs[2, 1].transAxes,
               size=20, weight='bold')
fig.legend(['Global Vision', 'Local Vision'], loc='upper right', fontsize=12)
# Display the plot
plt.show()
