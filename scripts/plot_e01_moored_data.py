import matplotlib.pyplot as plt
import matplotlib
import os
import pandas as pd
import numpy as np
import datetime
from tqdm import trange

VARS = ['Temperature', 'Salinity', 'Oxygen:Dissolved:SBE']
BIN_DEPTHS = [35, 75, 95]  # Bin the data to +/- 5m around each bin centre
START_YEAR = 1979


def add_datetime(df: pd.DataFrame):
    """
    Add column containing datetime-format dates to pandas dataframe containing the observations
    :param df:
    :return:
    """
    # Need to replace the slash in YYYY/mm/dd format with a dash to comply with ISO format
    # so YYYY-mm-dd
    df['Date'] = [x.replace('/', '-') for x in df['Date']]
    df['Datetime'] = [
        datetime.datetime.fromisoformat(d + ' ' + t)
        for d, t in zip(df['Date'], df['Time'])
    ]
    return df


def plot_annual_samp_freq(df: pd.DataFrame, var: str, output_dir: str):
    """
    Plot histogram of annual counts of observations
    :param output_dir:
    :param df:
    :param var:
    :return:
    """
    # Make a mask for the specific variable and use data in it for the plot
    var_mask = ~df.loc[:, var].isna()
    # https://stackoverflow.com/questions/42379818/correct-way-to-set-new-column-in-pandas-dataframe-to-avoid-settingwithcopywarnin
    df_masked = df.loc[var_mask, :].copy()
    df_masked.reset_index(drop=True, inplace=True)

    # Get number of files - have both .CUR and .cur, and .CTD and .ctd file suffixes
    ctd_mask = [x.lower().endswith('.ctd') for x in df_masked.loc[:, 'Filename']]
    cur_mask = [x.lower().endswith('.cur') for x in df_masked.loc[:, 'Filename']]
    num_ctd_files = len(np.unique(df_masked.loc[ctd_mask, 'Filename']))
    num_cur_files = len(np.unique(df_masked.loc[cur_mask, 'Filename']))

    # Access datetime.datetime properties
    # df_masked['Month'] = [x.month for x in df_masked.loc[:, 'Datetime'].copy()]
    df_masked['Year'] = [x.year for x in df_masked.loc[:, 'Datetime'].copy()]
    min_year = df_masked['Year'].min()
    max_year = df_masked['Year'].max()
    num_bins = max_year - min_year + 1

    # Create a new 2d array to hold the data
    # Need to pad whichever record is shorter to match the length of the other one
    # between the current meter record and the ctd record
    arr_length = sum(ctd_mask) if sum(ctd_mask) > sum(cur_mask) else sum(cur_mask)
    padded_cur_arr = np.append(df_masked.loc[cur_mask, 'Year'].to_numpy(),
                               np.repeat(np.nan, arr_length - sum(cur_mask)))
    padded_ctd_arr = np.append(df_masked.loc[ctd_mask, 'Year'].to_numpy(),
                               np.repeat(np.nan, arr_length - sum(ctd_mask)))
    year_array = np.vstack((padded_cur_arr, padded_ctd_arr)).T  # Need transpose to get 2 columns for histogram

    # # Manually assign y-axis ticks to have only whole number ticks
    # num_yticks = df_masked['Year'].max()

    # if num_yticks < 10:
    #     yticks = np.arange(num_yticks + 1)

    plt.clf()  # Clear any active plots
    fig, ax = plt.subplots()  # Create a new figure and axis instance

    # Plot ctd data on top of cur data in different colours
    # ax.hist(df_masked.loc[:, 'Year'], bins=num_bins, align='left',
    #         label='Number of CUR files: {}\nNumber of CTD files: {}'.format(num_cur_files,
    #                                                                         num_ctd_files))
    ax.hist(year_array, bins=num_bins, align='left', stacked=True, histtype='bar',
            label=[f'Number of CUR files: {num_cur_files}',
                   f'Number of CTD files: {num_ctd_files}'],
            color=['orange', 'b'])

    var = var.split(':')[0]  # Remove colons from oxygen
    ax.minorticks_on()
    ax.set_ylabel('Number of Measurements')
    ax.set_title(var, loc='left')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'e01_{var}_annual_sampling_counts.png'))
    plt.close(fig)
    return


def plot_monthly_samp_freq(df: pd.DataFrame, var: str, output_dir: str):
    """
    Plot monthly numbers of observations.
    Credit: James Hannah
    :param output_dir: path to folder for outputs
    :param df: pandas dataframe containing the raw data
    :param var: name of variable to use
    :return:
    """
    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    # Make a mask for the specific variable and use data in it for the plot
    var_mask = ~df.loc[:, var].isna()
    # https://stackoverflow.com/questions/42379818/correct-way-to-set-new-column-in-pandas-dataframe-to-avoid-settingwithcopywarnin
    df_masked = df.loc[var_mask, :].copy()
    df_masked.reset_index(drop=True, inplace=True)

    # Access datetime.datetime properties
    df_masked['Month'] = [x.month for x in df_masked.loc[:, 'Datetime'].copy()]
    df_masked['Year'] = [x.year for x in df_masked.loc[:, 'Datetime'].copy()]
    min_year = START_YEAR  # df_masked['Year'].min() Make the same for all of T, S, O
    max_year = df_masked['Year'].max()
    year_range = max_year - min_year + 1

    # Initialize array to hold heatmap data
    monthly_counts = np.zeros(
        shape=(year_range, len(months)), dtype='int')

    # Populate the above array
    for i in range(year_range):
        for j in range(len(months)):
            monthly_counts[i, j] = sum(
                (df_masked['Year'].values == min_year + i) &
                (df_masked['Month'].values == j + 1))

    # Max counts for setting limit of plot colour bar
    max_counts = np.max(monthly_counts)

    plt.clf()  # Close any open active plots
    matplotlib.rc("axes", titlesize=25)
    matplotlib.rc("xtick", labelsize=20)
    matplotlib.rc("ytick", labelsize=20)

    figsize = (40, 8)

    plt.figure(figsize=figsize, constrained_layout=True)

    # Display data as an image, i.e., on a 2D regular raster.
    plt.imshow(monthly_counts.T, vmin=0, vmax=max_counts, cmap="Blues")
    plt.yticks(ticks=range(12), labels=months)
    plt.xticks(
        ticks=range(0, year_range, 2),
        labels=range(min_year, max_year + 1, 2),
        rotation=45,
        ha="right",
        rotation_mode="anchor",
    )

    # Add observation count to each cell in the grid
    for i in range(year_range):
        for j in range(len(months)):
            plt.text(
                i,  # position to place the text
                j,  # "                        "
                monthly_counts[i, j],  # the text (number of profiles)
                ha="center",
                va="center",
                color="k",
                fontsize="large",
            )

    var = var.split(':')[0]
    plt.title(var, loc='left')
    plt.tight_layout()
    plt.colorbar()

    output_file = os.path.join(output_dir, f'e01_{var}_monthly_sampling_counts.png')
    plt.savefig(output_file)
    plt.close()

    # Reset values
    matplotlib.rcdefaults()
    plt.axis("auto")

    return


def plot_raw_TS_by_inst(df: pd.DataFrame, output_dir: str):
    # Create masks based on instrument type
    # Get number of files - have both .CUR and .cur, and .CTD and .ctd file suffixes
    ctd_mask = np.array([x.lower().endswith('.ctd') for x in df.loc[:, 'Filename']])
    cur_mask = np.array([x.lower().endswith('.cur') for x in df.loc[:, 'Filename']])

    units = ['C', 'PSS-78', 'mL/L']
    y_axis_limits = [(4, 19), (26, 38), (0, 7.5)]
    for depth in BIN_DEPTHS:
        # Make a mask to capture data within 5 vertical meters of each bin depth
        depth_mask = (df.loc[:, 'Depth'].to_numpy() >= depth - 5) & (df.loc[:, 'Depth'].to_numpy() <= depth + 5)

        for i, var in enumerate(VARS[:2]):
            # Make plot with 3 subplots
            fig, ax = plt.subplots(2, figsize=(10, 7), sharex=True)

            ax[0].scatter(df.loc[cur_mask & depth_mask, 'Datetime'].to_numpy(),
                          df.loc[cur_mask & depth_mask, var].to_numpy(),
                          marker='.', s=2, c='orange', label=f'CUR {var}')
            ax[1].scatter(df.loc[ctd_mask & depth_mask, 'Datetime'].to_numpy(),
                          df.loc[ctd_mask & depth_mask, var].to_numpy(),
                          marker='.', s=2, c='blue', label=f'CTD {var}')

            for j in [0, 1]:
                ax[j].set_ylabel(f'{var} ({units[i]})')

                ax[j].legend(loc='upper left', scatterpoints=3)

                ax[j].set_ylim(y_axis_limits[i])

                # Make ticks point inward and on all sides
                ax[j].tick_params(which='major', direction='in',
                                  bottom=True, top=True, left=True, right=True)

            plt.suptitle(f'Station E01 - {depth} m')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f'e01_raw_{var}_{depth}m_cur_vs_ctd.png'))
            plt.close(fig)
    return


def plot_raw_time_series(df: pd.DataFrame, output_dir: str):
    """
    Plot raw time series of temperature, salinity, and oxygen at selected depths
    Bin the data to 10m bins centred on the depths specified in BIN_DEPTHS
    Differentiate by colour the data from current meters and from CTDs
    :param df:
    :param output_dir:
    :return:
    """
    # Create masks based on instrument type
    # Get number of files - have both .CUR and .cur, and .CTD and .ctd file suffixes
    ctd_mask = np.array([x.lower().endswith('.ctd') for x in df.loc[:, 'Filename']])
    cur_mask = np.array([x.lower().endswith('.cur') for x in df.loc[:, 'Filename']])

    units = ['C', 'PSS-78', 'mL/L']
    y_axis_limits = [(4, 19), (26, 38), (0, 7.5)]
    for depth in BIN_DEPTHS:
        # Make a mask to capture data within 5 vertical meters of each bin depth
        depth_mask = (df.loc[:, 'Depth'].to_numpy() >= depth - 5) & (df.loc[:, 'Depth'].to_numpy() <= depth + 5)
        if depth == 75:  # No oxygen at this level for all time
            num_subplots = 2
            figsize = (10, 7)
        else:
            num_subplots = 3
            figsize = (10, 10)
        # Make plot with 3 subplots
        fig, ax = plt.subplots(num_subplots, figsize=figsize, sharex=True)
        for i, var in enumerate(VARS[:num_subplots]):
            # Plot CUR data
            ax[i].scatter(df.loc[cur_mask & depth_mask, 'Datetime'].to_numpy(),
                          df.loc[cur_mask & depth_mask, var].to_numpy(),
                          marker='.', s=2, c='orange', label=f'CUR {var}')
            # Plot CTD data in a different colour
            ax[i].scatter(df.loc[ctd_mask & depth_mask, 'Datetime'].to_numpy(),
                          df.loc[ctd_mask & depth_mask, var].to_numpy(),
                          marker='.', s=2, c='b', label=f'CTD {var}')
            ax[i].legend(loc='upper left', scatterpoints=3)  # Increase number of marker points in the legend
            ax[i].set_ylim(y_axis_limits[i])
            var = var.split(':')[0]
            ax[i].set_ylabel(f'{var} ({units[i]})')
            ax[i].set_title(var)
            # Make ticks point inward and on all sides
            ax[i].tick_params(which='major', direction='in',
                              bottom=True, top=True, left=True, right=True)
            ax[i].tick_params(which='minor', direction='in',
                              bottom=True, top=True, left=True, right=True)

        plt.suptitle(f'Station E01 - {depth} m')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'e01_raw_tso_{depth}m.png'))
        plt.close(fig)
    return


def compute_daily_means(df: pd.DataFrame, output_dir: str):
    """
    Compute daily means for temperature and salinity data
    :param output_dir:
    :param df:
    :return:
    """
    # obs_dates will be string type
    unique_dates, indices = np.unique(df['Date'], return_index=True)
    unique_datetimes = df.loc[indices, 'Datetime']
    # obs_days_of_year = np.array([x.timetuple().tm_yday for x in df.loc[indices, 'Datetime']])

    # Initialize an array to hold the daily means for each of the three binned depths
    daily_means_T = np.zeros((len(BIN_DEPTHS), len(unique_dates)))
    daily_means_S = np.zeros((len(BIN_DEPTHS), len(unique_dates)))

    # Iterate through the depths 35, 75, 95m
    for i in range(len(BIN_DEPTHS)):
        depth = BIN_DEPTHS[i]
        print(depth)
        # Make a mask to capture data within 5 vertical meters of each bin depth
        depth_mask = (df.loc[:, 'Depth'].to_numpy() >= depth - 5) & (df.loc[:, 'Depth'].to_numpy() <= depth + 5)
        # Iterate through all the unique dates of observation
        for k in trange(len(unique_dates)):
            date = unique_dates[k]
            date_mask = df.loc[:, 'Date'].to_numpy() == date
            # Populate the arrays for temperature and salinity
            daily_means_T[i, k] = df.loc[depth_mask & date_mask, 'Temperature'].mean()
            daily_means_S[i, k] = df.loc[depth_mask & date_mask, 'Salinity'].mean()

    # Save daily means to a file
    df_daily_mean = pd.DataFrame({'Datetime': unique_datetimes,
                                  'Temperature_35m': daily_means_T[0],
                                  'Temperature_75m': daily_means_T[1],
                                  'Temperature_95m': daily_means_T[2],
                                  'Salinity_35m': daily_means_S[0],
                                  'Salinity_75m': daily_means_S[1],
                                  'Salinity_95m': daily_means_S[2]})
    df_daily_mean.to_csv(os.path.join(output_dir, 'e01_daily_mean_TS_data.csv'), index=False)

    return unique_datetimes, daily_means_T, daily_means_S


def plot_daily_means(unique_datetimes, daily_means_T, daily_means_S, output_dir: str):
    range_T = (np.nanmin(daily_means_T) - 0.5, np.nanmax(daily_means_T) + 0.5)
    range_S = (np.nanmin(daily_means_S) - 0.5, np.nanmax(daily_means_S) + 0.5)

    # Plot the data
    for i, depth in enumerate(BIN_DEPTHS):
        fig, ax = plt.subplots(2, figsize=(10, 7), sharex=True)

        ax[0].scatter(unique_datetimes, daily_means_T[i], c='tab:red', marker='.', s=2,
                      label='Daily Mean Temperature')
        # ax[0].set_title('Daily Mean Temperature')
        ax[0].set_ylim(range_T)
        ax[0].set_ylabel('Temperature (C)')

        ax[1].scatter(unique_datetimes, daily_means_S[i], c='tab:blue', marker='.', s=2,
                      label='Daily Mean Salinity')
        # ax[1].set_title('Salinity')
        ax[1].set_ylim(range_S)
        ax[1].set_ylabel('Salinity (PSS-78)')

        ax[0].legend(loc='upper left', scatterpoints=3)
        ax[1].legend(loc='upper left', scatterpoints=3)

        # Make ticks point inward and on all sides
        for ax_j in [0, 1]:
            ax[ax_j].tick_params(which='major', direction='in',
                                 bottom=True, top=True, left=True, right=True)
            ax[ax_j].tick_params(which='minor', direction='in',
                                 bottom=True, top=True, left=True, right=True)

        plt.suptitle(f'Station E01 - {depth} m')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'e01_daily_mean_ts_{depth}m.png'))
        plt.close(fig)
    return


def compute_daily_clim(df_daily_mean: pd.DataFrame):
    """
    Compute 1990-2020 climatology for temperature and salinity
    :param df_daily_mean:
    :return:
    """
    days_of_year = np.arange(1, 365 + 1)
    df_daily_mean['Day_of_year'] = np.array(
        [
            x.timetuple().tm_yday for x in df_daily_mean.loc[:, 'Datetime']
        ]
    )

    # Make mask for years 1990-2020 ONLY
    year_range_mask = np.array([1990 <= x.year <= 2020 for x in df_daily_mean.loc[:, 'Datetime']])

    # Initialize arrays for containing temperature and salinity climatological values
    daily_clim_T = np.zeros((len(BIN_DEPTHS), len(days_of_year)))
    daily_clim_S = np.zeros((len(BIN_DEPTHS), len(days_of_year)))

    # Populate the daily climatology array
    for i, depth in enumerate(BIN_DEPTHS):
        for day_num in days_of_year:
            day_num_mask = df_daily_mean.loc[:, 'Day_of_year'].to_numpy() == day_num

            daily_clim_T[i, day_num - 1] = df_daily_mean.loc[
                day_num_mask & year_range_mask, f'Temperature_{depth}m'
            ].mean()
            daily_clim_S[i, day_num - 1] = df_daily_mean.loc[
                day_num_mask & year_range_mask, f'Salinity_{depth}m'
            ].mean()

    return days_of_year, daily_clim_T, daily_clim_S


def plot_daily_clim(df_daily_mean: pd.DataFrame, output_dir: str):
    """
    Plot daily climatology for 1990-2020
    :param df_daily_mean:
    :param output_dir:
    :return:
    """
    days_of_year, daily_clim_T, daily_clim_S = compute_daily_clim(df_daily_mean)

    range_T = (np.nanmin(daily_clim_T) - 0.5, np.nanmax(daily_clim_T) + 0.5)
    range_S = (np.nanmin(daily_clim_S) - 0.5, np.nanmax(daily_clim_S) + 0.5)

    for i, depth in enumerate(BIN_DEPTHS):
        fig, ax = plt.subplots(2, figsize=(10, 7), sharex=True)

        ax[0].plot(days_of_year, daily_clim_T[i, :], c='tab:red',
                   label='Temperature Climatology')
        ax[1].plot(days_of_year, daily_clim_S[i, :], c='tab:blue',
                   label='Salinity Climatology')

        ax[0].legend(loc='upper left', scatterpoints=3)
        ax[1].legend(loc='upper left', scatterpoints=3)

        ax[0].set_ylabel('Temperature (C)')
        ax[1].set_ylabel('Salinity (PSS-78)')

        ax[0].set_ylim(range_T)
        ax[1].set_ylim(range_S)

        ax[1].set_xlabel('Day of Year')

        # Make ticks point inward and on all sides
        for ax_j in [0, 1]:
            ax[ax_j].tick_params(which='major', direction='in',
                                 bottom=True, top=True, left=True, right=True)
            ax[ax_j].tick_params(which='minor', direction='in',
                                 bottom=True, top=True, left=True, right=True)

        # Save figure
        plt.suptitle(f'Station E01 - {depth} m')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'e01_climatology_1990-2020_ts_{depth}m.png'))
        plt.close(fig)

    return


def compute_daily_anom(df_daily_mean: pd.DataFrame):
    """
    Compute daily mean anomalies from daily mean data and daily climatologies
    :param df_daily_mean:
    :return:
    """
    # Compute daily climatologies
    days_of_year, daily_clim_T, daily_clim_S = compute_daily_clim(df_daily_mean)

    df_daily_mean['Day_of_year'] = np.array(
        [
            x.timetuple().tm_yday for x in df_daily_mean.loc[:, 'Datetime']
        ]
    )

    # Subtract the daily climatologies from the daily mean data
    df_anom = pd.DataFrame({'Datetime': df_daily_mean['Datetime'],
                            'Temperature_35m': np.repeat(np.nan, len(df_daily_mean)),
                            'Temperature_75m': np.repeat(np.nan, len(df_daily_mean)),
                            'Temperature_95m': np.repeat(np.nan, len(df_daily_mean)),
                            'Salinity_35m': np.repeat(np.nan, len(df_daily_mean)),
                            'Salinity_75m': np.repeat(np.nan, len(df_daily_mean)),
                            'Salinity_95m': np.repeat(np.nan, len(df_daily_mean))})

    for i, depth in enumerate(BIN_DEPTHS):
        # Iterate through the days of year in 1-365
        for day_num in days_of_year:
            # Create a mask for the day of year
            day_mask = df_daily_mean.loc[:, 'Day_of_year'].to_numpy() == day_num
            # Index day-1 because day starts at 1 and python indexing starts at zero
            df_anom.loc[
                day_mask, f'Temperature_{depth}m'
            ] = df_daily_mean.loc[:, f'Temperature_{depth}m'] - daily_clim_T[i, day_num - 1]
            df_anom.loc[
                day_mask, f'Salinity_{depth}m'
            ] = df_daily_mean.loc[:, f'Salinity_{depth}m'] - daily_clim_S[i, day_num - 1]

    return df_anom


def plot_daily_anom(df_daily_mean: pd.DataFrame, output_dir: str):
    """
    Compute daily mean anomalies from daily mean data and daily climatologies
    :return:
    """
    df_anom = compute_daily_anom(df_daily_mean)

    # Make plots for separate depths

    # Make the ranges centred on zero
    abs_max_T = np.nanmax(
        df_anom.loc[:, ['Temperature_35m', 'Temperature_75m', 'Temperature_95m']].abs()
    )
    abs_max_S = np.nanmax(
        df_anom.loc[:, ['Salinity_35m', 'Salinity_75m', 'Salinity_95m']].abs()
    )
    range_T = (-abs_max_T - 0.5, abs_max_T + 0.5)
    range_S = (-abs_max_S - 0.5, abs_max_S + 0.5)

    for i, depth in enumerate(BIN_DEPTHS):
        fig, ax = plt.subplots(2, figsize=(10, 7), sharex=True)

        ax[0].scatter(df_anom.loc[:, 'Datetime'], df_anom.loc[:, f'Temperature_{depth}m'],
                      c='tab:red', marker='.', s=2, label='Temperature Anomalies')
        ax[1].scatter(df_anom.loc[:, 'Datetime'], df_anom.loc[:, f'Salinity_{depth}m'],
                      c='tab:blue', marker='.', s=2, label='Salinity Anomalies')

        ax[0].set_ylabel('Temperature (C)')
        ax[1].set_ylabel('Salinity (PSS-78)')

        ax[0].set_ylim(range_T)
        ax[1].set_ylim(range_S)

        # ax[0].set_title('Temperature Anomalies')
        # ax[1].set_title('Salinity Anomalies')

        ax[0].legend(loc='upper left', scatterpoints=3)
        ax[1].legend(loc='upper left', scatterpoints=3)

        # Make ticks point inward and on all sides
        for ax_j in [0, 1]:
            ax[ax_j].tick_params(which='major', direction='in',
                                 bottom=True, top=True, left=True, right=True)
            ax[ax_j].tick_params(which='minor', direction='in',
                                 bottom=True, top=True, left=True, right=True)

        # Save figure
        plt.suptitle(f'Station E01 - {depth} m')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'e01_daily_anom_ts_{depth}m.png'))
        plt.close(fig)
    return


def plot_monthly_means(df: pd.DataFrame, output_dir: str):
    return


def plot_monthly_clim():
    return


def plot_monthly_anom():
    return


def run_plot(
        do_monthly_avail: bool = False,
        do_annual_avail: bool = False,
        do_raw_by_inst: bool = False,
        do_raw: bool = False,
        do_daily_means: bool = False,
        do_daily_clim: bool = False,
        do_daily_anom: bool = False,
        do_monthly_means: bool = False,
        do_monthly_clim: bool = False,
        do_monthly_anom: bool = False
):
    """

    :param do_monthly_avail: Plot monthly observation counts
    :param do_annual_avail: Plot annual observation counts
    :param do_raw_by_inst: Plot
    :param do_raw:
    :param do_daily_means:
    :param do_daily_clim:
    :param do_daily_anom:
    :param do_monthly_means:
    :param do_monthly_clim:
    :param do_monthly_anom:
    :return:
    """
    old_dir = os.getcwd()
    if os.path.basename(old_dir) == 'scripts':
        new_dir = os.path.dirname(old_dir)
    elif os.path.basename(old_dir) == 'e01_mooring_data':
        new_dir = old_dir
        old_dir = os.path.join(new_dir, 'scripts')
    os.chdir(new_dir)
    output_dir = os.path.join(new_dir, 'figures')

    # Files are too big to store in the github project directory
    data_dir = 'E:\\charles\\e01_data_page\\csv_data\\'

    file_list = [data_dir + 'e01_cur_data_all.csv', data_dir + 'e01_ctd_data.csv']

    # Only keep current meter data before 2007 since 2008 is when CTD data start
    if do_raw_by_inst:
        df_all = pd.concat((pd.read_csv(file_list[0]), pd.read_csv(file_list[1])))
    else:
        cur_data = pd.read_csv(file_list[0])
        cur_data_pre2007 = cur_data.loc[cur_data['Date'].to_numpy() < '2007', :]
        df_all = pd.concat((cur_data_pre2007, pd.read_csv(file_list[1])))

    # Reset the index in the dataframe
    df_all.reset_index(drop=True, inplace=True)

    # Add datetime-format date for plotting ease
    df_dt = add_datetime(df_all)

    if do_monthly_avail:
        print('Plotting monthly data availability ...')
        for var in VARS:
            plot_monthly_samp_freq(df_dt, var, output_dir)

    if do_annual_avail:
        print('Plotting annual data availability ...')
        for var in VARS:
            plot_annual_samp_freq(df_dt, var, output_dir)

    if do_raw_by_inst:
        print('Plotting raw data by instrument ...')
        plot_raw_TS_by_inst(df_dt, output_dir)

    if do_raw:
        print('Plotting raw data combining CTD and CUR data ...')
        plot_raw_time_series(df_dt, output_dir)

    if do_daily_means:
        print('Plotting daily mean data ...')
        daily_means_file = os.path.join(new_dir, 'data', 'e01_daily_mean_TS_data.csv')
        if not os.path.exists(daily_means_file):
            unique_datetimes, daily_means_T, daily_means_S = compute_daily_means(df_dt, output_dir)
        else:
            df_daily_means = pd.read_csv(daily_means_file)
            unique_datetimes = df_daily_means.loc[:, 'Datetime'].to_numpy()
            # Fix formatting - convert from string/object to datetime.datetime
            unique_datetimes = [
                datetime.datetime.fromisoformat(x.split(' ')[0]) for x in unique_datetimes
            ]
            daily_means_T = df_daily_means.loc[
                            :, ['Temperature_35m', 'Temperature_75m', 'Temperature_95m']
                            ].to_numpy().T
            daily_means_S = df_daily_means.loc[
                            :, ['Salinity_35m', 'Salinity_75m', 'Salinity_95m']
                            ].to_numpy().T

        plot_daily_means(unique_datetimes, daily_means_T, daily_means_S, output_dir)

    if do_daily_clim:
        print('Plotting daily T and S climatologies ...')
        daily_means_file = os.path.join(new_dir, 'data', 'e01_daily_mean_TS_data.csv')
        if not os.path.exists(daily_means_file):
            unique_datetimes, daily_means_T, daily_means_S = compute_daily_means(
                df_dt, output_dir
            )
        df_daily_means = pd.read_csv(daily_means_file)
        # Fix formatting
        df_daily_means.loc[:, 'Datetime'] = [
            datetime.datetime.fromisoformat(x.split(' ')[0]) for x in
            df_daily_means['Datetime']
        ]
        # Plot climatologies
        plot_daily_clim(df_daily_means, output_dir)

    if do_daily_anom:
        print('Plotting daily mean anomalies ...')
        daily_means_file = os.path.join(new_dir, 'data', 'e01_daily_mean_TS_data.csv')
        if not os.path.exists(daily_means_file):
            unique_datetimes, daily_means_T, daily_means_S = compute_daily_means(
                df_dt, output_dir
            )
        df_daily_means = pd.read_csv(daily_means_file)
        # Fix formatting
        df_daily_means.loc[:, 'Datetime'] = [
            datetime.datetime.fromisoformat(x.split(' ')[0]) for x in
            df_daily_means['Datetime']
        ]
        plot_daily_anom(df_daily_means, output_dir)

    # Reset the current directory
    os.chdir(old_dir)

    return
