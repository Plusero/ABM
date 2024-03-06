import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Use scientific style for the plot
plt.style.use('seaborn-whitegrid')

# Read the Excel file as a DataFrame, use the header=6 to locate the column names
df = pd.read_excel('min-distance-to-herd-global-local-table.xlsx', header=6)
df_global = df[df['global-vision'] == True]
df_local = df[df['global-vision'] == False]

# Extract specific columns
ticks_global = df_global['ticks']
ticks_local = df_local['ticks']
distance_traveled_global = df_global['distance-traveled of robots']
distance_traveled_local = df_local['distance-traveled of robots']
furthest_allowed_global = df_global['min-distance-to-herd']
furthest_allowed_local = df_local['min-distance-to-herd']

# For each value of bot-speed-ratio, calculate how many of them have value of ticks smaller than 10000
filtered_df_global = df_global[df_global['ticks'] < 10000]
filtered_counts_global = filtered_df_global['min-distance-to-herd'].value_counts()
filtered_df_local = df_local[df_local['ticks'] < 10000]
filtered_counts_local = filtered_df_local['min-distance-to-herd'].value_counts()

# Calculate the total counts of each 'min-distance-to-herd' value
total_counts_global = df_global['min-distance-to-herd'].value_counts()
total_counts_local = df_local['min-distance-to-herd'].value_counts()
ratio_global = filtered_counts_global / total_counts_global
ratio_global = ratio_global.fillna(0)
ratio_local = filtered_counts_local / total_counts_local
ratio_local = ratio_local.fillna(0)

grouped_global = filtered_df_global.groupby(
    'min-distance-to-herd')['distance-traveled of robots']
mean_distance_global = grouped_global.mean()
std_distance_global = grouped_global.std()
grouped_local = filtered_df_local.groupby(
    'min-distance-to-herd')['distance-traveled of robots']
mean_distance_local = grouped_local.mean()
std_distance_local = grouped_local.std()

grouped_ticks_global = df_global.groupby('min-distance-to-herd')['ticks']
mean_ticks_global = grouped_ticks_global.mean()
std_ticks_global = grouped_ticks_global.std()
grouped_ticks_local = df_local.groupby('min-distance-to-herd')['ticks']
mean_ticks_local = grouped_ticks_local.mean()
std_ticks_local = grouped_ticks_local.std()

# Create a figure and a set of subplots
fig, axs = plt.subplots(3, 1, sharex='col')
plt.subplots_adjust(hspace=0.3)

# draw scatter plots for the success rate
axs[0].plot(ratio_global.index, ratio_global, 'o:', label='Global Vision')
axs[0].plot(ratio_local.index, ratio_local, 'o-', label='Local Vision')
# axs[0].set_xlabel('min-distance-to-herd', fontsize=12)
axs[0].set_ylabel('Success Rate', fontsize=12)
axs[0].set_xticks(np.arange(min(ratio_global.index),
                  max(ratio_global.index)+1, 1))


axs[1].errorbar(mean_distance_global.index, mean_distance_global,
                yerr=std_distance_global, fmt='o:', capsize=6, label='Global Vision')
axs[1].errorbar(mean_distance_local.index, mean_distance_local,
                yerr=std_distance_local, fmt='o-', capsize=6, label='Local Vision')
# axs[1].set_xlabel('min-distance-to-herd', fontsize=12)
axs[1].set_ylabel('Distance Traveled', fontsize=12)
xticks_a = axs[0].get_xticks()
axs[1].set_xticks(xticks_a)


axs[2].errorbar(mean_ticks_global.index, mean_ticks_global,
                yerr=std_ticks_global, fmt='o:', capsize=6, label='Global Vision')
axs[2].errorbar(mean_ticks_local.index, mean_ticks_local,
                yerr=std_ticks_local, fmt='o-', capsize=6, label='Local Vision')
axs[2].set_xlabel('min-distance-to-herd', fontsize=12)
axs[2].set_ylabel('Time to Finish', fontsize=12)
axs[2].set_xticks(xticks_a)


axs[0].text(-0.12, 1, 'a', transform=axs[0].transAxes,
            size=20, weight='bold')
axs[1].text(-0.12, 1, 'b', transform=axs[1].transAxes,
            size=20, weight='bold')
axs[2].text(-0.12, 1, 'c', transform=axs[2].transAxes,
            size=20, weight='bold')
fig.legend(['Global Vision', 'Local Vision'], loc='upper right', fontsize=12)

# Display the plot
plt.show()
