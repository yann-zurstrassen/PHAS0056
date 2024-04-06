import numpy as np
import time
from copy import deepcopy
import math
import matplotlib.pyplot as plt

from matplotlib.ticker import AutoMinorLocator
from matplotlib.offsetbox import AnchoredText
from matplotlib.text import OffsetFrom
from matplotlib.lines import Line2D

from sklearn import preprocessing


##########################
#ATLAS Analysis Functions#
##########################

class_names_grouped = ['VH -> Vbb','Diboson','ttbar','Single top', 'W+(bb,bc,cc,bl)','W+cl','W+ll','Z+(bb,bc,cc,bl)',
                       'Z+cl','Z+ll'
                       ]

class_names_map = {'VH -> Vbb':['ggZllH125','ggZvvH125','qqWlvH125', 'qqZllH125', 'qqZvvH125'],
    'Diboson':['WW','ZZ','WZ'],
    'ttbar':['ttbar'],
    'Single top':['stopWt','stops','stopt'],
    'W+(bb,bc,cc,bl)':['Wbb','Wbc','Wcc','Wbl'],
    'W+cl':['Wcl'],
    'W+ll':['Wl'],
    'Z+(bb,bc,cc,bl)':['Zbb','Zbc','Zcc','Zbl'],
    'Z+cl':['Zcl'],
    'Z+ll':['Zl']
}

colour_map = {'VH -> Vbb':'#FF0000',
    'Diboson':'#999999',
    'ttbar':'#FFCC00',
    'Single top':'#CC9900',
    'W+(bb,bc,cc,bl)':'#006600',
    'W+cl':'#66CC66',
    'W+ll':'#99FF99',
    'Z+(bb,bc,cc,bl)':'#0066CC',
    'Z+cl':'#6699CC',
    'Z+ll':'#99CCFF'
}

legend_names = [r'VH $\rightarrow$ Vbb','Diboson',r"t$\bar t$",'Single top', 'W+(bb,bc,cc,bl)','W+cl','W+ll','Z+(bb,bc,cc,bl)',
                'Z+cl','Z+ll'
                ]
def scale_prepare_data(df_train, df_val, df_test, variables, scaler='minmax'):
    '''
    Helper function to apply scaling of data and prepare it for training.
    Function takes as parameters the 3 dataframes containing test/validation/train data.
    A list of variables to be used for training is also required, as well as the scaling mode.
    
    Parameters:
        df_train - pandas dataframe containing training data
        df_val - pandas dataframe containing validation data
        df_test - pandas dataframe containing test data
        variables - list of strings of variables to be used for training
        scaler - string name of scaling mode. Only 'minmax', 'standard' and 'norm' are 
            supported. Default is 'minmax'.
    
    Returns:
        x_train - numpy array of scaled training data
        y_train - numpy array of training labels
        w_train - numpy array of training weights
        (x_val, y_val) - tuple of two numpy arrays containing scaled validation data 
            and labels. Returned as a tuple for easy use in model.fit
        (x_test, y_test) - tuple of two numpy arrays containing scaled test data
    
    
    '''
    if scaler == 'minmax':
        scaler = preprocessing.MinMaxScaler()
    elif scaler == 'standard':
        scaler = preprocessing.StandardScaler()
    else:
        raise ValueError(f'Scaler {scaler} not recognised. Only minmax and standard are supported.')

    # Calculate the scaling params
    scaler.fit(df_train[variables])
    
    x_train = scaler.transform(df_train[variables])
    y_train = df_train['Class'].values
    w_train = df_train['training_weight'].values
    
    x_val = scaler.transform(df_val[variables])
    y_val = df_val['Class'].values
    
    x_test = scaler.transform(df_test[variables])
    y_test = df_test['Class'].values
    
    return x_train, y_train, w_train, (x_val, y_val), (x_test, y_test)


def setBinCategory(df,bins):
    #function is used to assign the bin of the histogram each event is added to after sensitivity scaling
    if len(bins)!=21:
        print ("ONLY SET FOR 20 BINS")

    df['bin_scaled'] = 999
    bin_scaled_list = df['bin_scaled'].tolist()

    step = 2/(len(bins)-1)  #step between midpoints
    midpoint = -1 + step/2.0   #Initial midpoint
    decision_value_list = df['decision_value'].tolist()

    for j in range(len(bins)-1):
        for i in range(len(decision_value_list)):
            if ((decision_value_list[i] >= bins[j]) & (decision_value_list[i] < bins[j+1])):
                bin_scaled_list[i] = midpoint
        midpoint = midpoint + step

    df['bin_scaled'] = bin_scaled_list

    return df

def bdt_plot(df,z_s = 10,z_b = 10,show=False, block=False, trafoD_bins = False, bin_number = 20):
    """Plots histogram decision score output of classifier"""

    nJets = df['nJ'].tolist()[1]
    df['decision_value'] = ((df['decision_value']-0.5)*2)
    if trafoD_bins == True:
        bins, arg2, arg3 = trafoD_with_error(df)
        print(len(bins))
    else:
         bins = np.linspace(-1,1,bin_number+1)

    # Initialise plot stuff
    plt.ion()
    plt.close("all")
    fig = plt.figure(figsize=(8.5,7))
    plot_range = (-1, 1)
    plot_data = []
    plot_weights = []
    plot_colors = []
    plt.rc('font', weight='bold')
    plt.rc('xtick.major', size=5, pad=7)
    plt.rc('xtick', labelsize=10)

    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    plt.rcParams["mathtext.default"] = "regular"

    df = setBinCategory(df,bins)

    decision_value_list = df['bin_scaled'].tolist()
    post_fit_weight_list = df['post_fit_weight'].tolist()
    sample_list = df['sample'].tolist()

    # Get list of hists.
    for t in class_names_grouped[::-1]:
        class_names = class_names_map[t]
        class_decision_vals = []
        plot_weight_vals = []
        for c in class_names:
            for x in range(0,len(decision_value_list)):
                if sample_list[x] == c:
                    class_decision_vals.append(decision_value_list[x])
                    plot_weight_vals.append(post_fit_weight_list[x])

        plot_data.append(class_decision_vals)
        plot_weights.append(plot_weight_vals)
        plot_colors.append(colour_map[t])


    #Plots the filled in histogram parts
    plt.hist(plot_data,
             bins=bins,
             weights=plot_weights,
             range=plot_range,
             rwidth=1,
             color=plot_colors,
             label=legend_names[::-1],
             stacked=True,
             edgecolor='none')

    #Plots the additional line over the top for signal events
    if nJets == 2:
        multiplier = 20
    elif nJets == 3:
        multiplier = 100
    
    plt.plot([],[],color='#FF0000',label=r'VH $\rightarrow$ Vbb x '+str(multiplier))
    
    df_sig = df.loc[df['Class']==1]
    plt.hist(df_sig['bin_scaled'].tolist(),
         bins=bins,
         weights=(df_sig['post_fit_weight']*multiplier).tolist(),
         range=plot_range,
         rwidth=1,
         histtype = 'step',
         linewidth=2,
         color='#FF0000',
         edgecolor='#FF0000')

    #sets axis limits and labels
    x1, x2, y1, y2 = plt.axis()
    plt.yscale('log', nonposy='clip')       #can comment out this line if log error stops plotting
    plt.axis((x1, x2, y1, y2 * 1.2))
    axes = plt.gca()
    axes.set_ylim([5,135000])
    axes.set_xlim([-1,1])
    x = [-1,-0.8,-0.6,-0.4,-0.2,0,0.2,0.4,0.6,0.8,1]
    plt.xticks(x, x,fontweight = 'normal',fontsize = 20)
    y = [r"10",r"10$^{2}$",r"10$^{3}$",r"10$^{4}$",r"10$^{5}$"]
    yi = [10,100,1000,10000,100000]
    plt.yticks(yi, y,fontweight = 'normal',fontsize = 20)       #and this one 

    #sets axis ticks
    axes.yaxis.set_ticks_position('both')
    axes.yaxis.set_tick_params(which='major', direction='in', length=10, width=1)
    axes.yaxis.set_tick_params(which='minor', direction='in', length=5, width=1)
    axes.xaxis.set_ticks_position('both')
    axes.xaxis.set_tick_params(which='major', direction='in', length=10, width=1)
    axes.xaxis.set_tick_params(which='minor', direction='in', length=5, width=1)
    axes.xaxis.set_minor_locator(AutoMinorLocator(4))
    handles, labels = axes.get_legend_handles_labels()

    #hack thing to get legend entries in correct order
    handles = handles[::-1]
    handles = handles+handles
    handles = handles[1:12]

    plt.legend(loc='upper right', ncol=1, prop={'size': 12},frameon=False,
               handles=handles)

    #axis titles and lables
    plt.ylabel("Events",fontsize = 20,fontweight='normal')
    axes.yaxis.set_label_coords(-0.07,0.93)
    plt.xlabel(r"BDT$_{VH}$ output",fontsize = 20,fontweight='normal')
    axes.xaxis.set_label_coords(0.89, -0.07)
    an1 = axes.annotate("ATLAS Internal", xy=(0.05, 0.91), xytext=(0.05, 0.91), xycoords=axes.transAxes,fontstyle = 'italic',fontsize = 16)
    offset_from = OffsetFrom(an1, (0, -1.4))
    an2 = axes.annotate(r'$\sqrt{s}$' + " = 13 TeV , 36.1 fb$^{-1}$", xy=(0.05,0.91), xytext=(0.05, 0.91), xycoords=axes.transAxes, textcoords=offset_from, fontweight='normal',fontsize = 12)
    offset_from = OffsetFrom(an2, (0, -1.4))
    an3 = axes.annotate("1 lepton, "+str(nJets)+" jets, 2 b-tags", xy=(0.05,0.91), xytext=(0.05, 0.91), xycoords=axes.transAxes, textcoords=offset_from,fontstyle = 'italic',fontsize = 12)
    offset_from = OffsetFrom(an3, (0, -1.6))
    an4 = axes.annotate("p$^V_T \geq$ 150 GeV", xy=(0.05,0.91), xytext=(0.05, 0.91), xycoords=axes.transAxes, textcoords=offset_from,fontstyle = 'italic',fontsize = 12)

    plt.show(block=block)


    return fig,axes


def nn_output_plot(df,z_s = 10,z_b = 10,show=False, block=False, trafoD_bins = False, bin_number = 20):
    """Plots histogram decision score output of classifier"""

    nJets = df['nJ'].tolist()[1]
    df['decision_value'] = ((df['decision_value']-0.5)*2)
    if trafoD_bins == True:
        bins, arg2, arg3 = trafoD_with_error(df)
        print(len(bins))
    else:
         bins = np.linspace(-1,1,bin_number+1)

    # Initialise plot stuff
    plt.ion()
    plt.close("all")
    fig = plt.figure(figsize=(8.5,7))
    plot_range = (-1, 1)
    plot_data = []
    plot_weights = []
    plot_colors = []
    plt.rc('font', weight='bold')
    plt.rc('xtick.major', size=5, pad=7)
    plt.rc('xtick', labelsize=10)

    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    plt.rcParams["mathtext.default"] = "regular"

    df = setBinCategory(df,bins)

    decision_value_list = df['bin_scaled'].tolist()
    post_fit_weight_list = df['post_fit_weight'].tolist()
    sample_list = df['sample'].tolist()

    # Get list of hists.
    for t in class_names_grouped[::-1]:
        class_names = class_names_map[t]
        class_decision_vals = []
        plot_weight_vals = []
        for c in class_names:
            for x in range(0,len(decision_value_list)):
                if sample_list[x] == c:
                    class_decision_vals.append(decision_value_list[x])
                    plot_weight_vals.append(post_fit_weight_list[x])

        plot_data.append(class_decision_vals)
        plot_weights.append(plot_weight_vals)
        plot_colors.append(colour_map[t])


    #Plots the filled in histogram parts
    plt.hist(plot_data,
             bins=bins,
             weights=plot_weights,
             range=plot_range,
             rwidth=1,
             color=plot_colors,
             label=legend_names[::-1],
             stacked=True,
             edgecolor='none')

    #Plots the additional line over the top for signal events
    df_sig = df.loc[df['Class']==1]
    # Plot.
    if nJets == 2:
        
        multiplier = 20
    elif nJets == 3:
        multiplier = 100
    
    plt.plot([],[],color='#FF0000',label=r'VH $\rightarrow$ Vbb x '+str(multiplier))

    plt.hist(df_sig['bin_scaled'].tolist(),
         bins=bins,
         weights=(df_sig['post_fit_weight']*multiplier).tolist(),
         range=plot_range,
         rwidth=1,
         histtype = 'step',
         linewidth=2,
         color='#FF0000',
         edgecolor='#FF0000')

    #sets axis limits and labels
    x1, x2, y1, y2 = plt.axis()
    plt.yscale('log')   #can comment out this line if log error stops plotting
    y1 = 5 # make sure we don't set a non-positive y axis lim
    plt.axis((x1, x2, y1, y2 * 1.2))
    axes = plt.gca()
    axes.set_ylim([5,135000])
    axes.set_xlim([-1,1])
    x = [-1,-0.8,-0.6,-0.4,-0.2,0,0.2,0.4,0.6,0.8,1]
    plt.xticks(x, x,fontweight = 'normal',fontsize = 20)
    y = [r"10",r"10$^{2}$",r"10$^{3}$",r"10$^{4}$",r"10$^{5}$"]
    yi = [10,100,1000,10000,100000]
    plt.yticks(yi, y,fontweight = 'normal',fontsize = 20)   #and also this line

    #sets axis ticks
    axes.yaxis.set_ticks_position('both')
    axes.yaxis.set_tick_params(which='major', direction='in', length=10, width=1)
    axes.yaxis.set_tick_params(which='minor', direction='in', length=5, width=1)

    axes.xaxis.set_ticks_position('both')
    axes.xaxis.set_tick_params(which='major', direction='in', length=10, width=1)
    axes.xaxis.set_tick_params(which='minor', direction='in', length=5, width=1)

    axes.xaxis.set_minor_locator(AutoMinorLocator(4))
    handles, labels = axes.get_legend_handles_labels()


    #Hack thing to get legend entries in correct order
    handles = handles[::-1]
    handles = handles+handles
    handles = handles[1:12]

    plt.legend(loc='upper right', ncol=1, prop={'size': 12},frameon=False,
               handles=handles)

    #axis titles and lables
    plt.ylabel("Events",fontsize = 20,fontweight='normal')
    axes.yaxis.set_label_coords(-0.07,0.93)
    plt.xlabel(r"NN$_{VH}$ output",fontsize = 20,fontweight='normal')
    axes.xaxis.set_label_coords(0.89, -0.07)
    an1 = axes.annotate("ATLAS Internal", xy=(0.05, 0.91), xytext=(0.05, 0.91), xycoords=axes.transAxes,fontstyle = 'italic',fontsize = 16)

    offset_from = OffsetFrom(an1, (0, -1.4))
    an2 = axes.annotate(r'$\sqrt{s}$' + " = 13 TeV , 36.1 fb$^{-1}$", xy=(0.05,0.91), xytext=(0.05, 0.91), xycoords=axes.transAxes, textcoords=offset_from, fontweight='normal',fontsize = 12)

    offset_from = OffsetFrom(an2, (0, -1.4))
    an3 = axes.annotate("1 lepton, "+str(nJets)+" jets, 2 b-tags", xy=(0.05,0.91), xytext=(0.05, 0.91), xycoords=axes.transAxes, textcoords=offset_from,fontstyle = 'italic',fontsize = 12)

    offset_from = OffsetFrom(an3, (0, -1.6))
    an4 = axes.annotate("p$^V_T \geq$ 150 GeV", xy=(0.05,0.91), xytext=(0.05, 0.91), xycoords=axes.transAxes, textcoords=offset_from,fontstyle = 'italic',fontsize = 12)


    plt.show(block=block)


    return fig,axes



def plot_variable(df,variable, bins = None,bin_number = 20):
    """
    Takes a pandas df and plots a specific variable (mBB, Mtop etc)

    """

    nJets = 2

#     if bins == None:
#         bins = np.linspace(0,400,bin_number+1)
#     print(bins)
    # Initialise plot stuff
    bins = 20
    plt.ion()
    plt.close("all")
    fig = plt.figure(figsize=(8.5*1.2,7*1.2))
    plot_data = []
    plot_weights = []
    plot_colors = []
    plt.rc('font', weight='bold')
    plt.rc('xtick.major', size=5, pad=7)
    plt.rc('xtick', labelsize=10)

    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    plt.rcParams["mathtext.default"] = "regular"


    var_list = df[variable].tolist()

    if variable in ['mBB','Mtop','pTV','MET','mTW','pTB1','pTB2']:
        var_list = [i/1e3 for i in var_list]


    post_fit_weight_list = df['post_fit_weight'].tolist()
    sample_list = df['sample'].tolist()

    # Get list of hists.
    for t in class_names_grouped[::-1]:
        class_names = class_names_map[t]
        class_decision_vals = []
        plot_weight_vals = []
        for c in class_names:
            for x in range(0,len(var_list)):
                if sample_list[x] == c:
                    class_decision_vals.append(var_list[x])
                    plot_weight_vals.append(post_fit_weight_list[x])

        plot_data.append(class_decision_vals)
        plot_weights.append(plot_weight_vals)
        plot_colors.append(colour_map[t])

    multiplier = 20


    data = plt.hist(plot_data,
             bins=bins,
             weights=plot_weights,
             rwidth=1,
             color=plot_colors,
             label=legend_names[::-1],
             stacked=True,
             edgecolor='none')

    df_sig = df.loc[df['Class']==1]
    var_list_sig = df_sig[variable].tolist()


    if variable in ['mBB','Mtop','pTV','MET','mTW']:
        var_list_sig = [i/1e3 for i in var_list_sig]
    plt.hist(var_list_sig,
         bins=bins,
         weights=(df_sig['post_fit_weight']*multiplier).tolist(),
         rwidth=1,
         histtype = 'step',
         linewidth=2,
         color='#FF0000',
         edgecolor='#FF0000')
    plt.plot([],[],color='#FF0000',label=r'VH $\rightarrow$ Vbb x '+str(multiplier))

    x1, x2, y1, y2 = plt.axis()
    axes = plt.gca()
    plt.xticks(fontweight = 'normal',fontsize = 20)
    plt.yticks(fontweight = 'normal',fontsize = 20)

    axes.yaxis.set_ticks_position('both')
    axes.yaxis.set_tick_params(which='major', direction='in', length=10, width=1)
    axes.yaxis.set_tick_params(which='minor', direction='in', length=5, width=1)

    axes.xaxis.set_ticks_position('both')
    axes.xaxis.set_tick_params(which='major', direction='in', length=10, width=1)
    axes.xaxis.set_tick_params(which='minor', direction='in', length=5, width=1)

    axes.xaxis.set_minor_locator(AutoMinorLocator(4))
    handles, labels = axes.get_legend_handles_labels()


    handles = handles[::-1]
    handles = handles+handles
    handles = handles[1:12]

    plt.legend(loc='upper right', ncol=1, prop={'size': 12},frameon=False,
               handles=handles)

    plt.ylabel("Events",fontsize = 20,fontweight='normal')
    axes.yaxis.set_label_coords(-0.07,0.93)
    label = variable
    if variable == 'mBB':
        label = r"$m_{bb}$ GeV"
    elif variable == 'Mtop':
        label = r"$m_{top}$ GeV"

    plt.xlabel(label,fontsize = 20,fontweight='normal')
    axes.xaxis.set_label_coords(0.89, -0.07)

    plt.show()


def sensitivity_cut_based(df):
    """Calculate sensitivity from dataframe with error"""

    # Initialise sensitivity and error.
    sens_sq = 0
    bins = np.arange(20*1e3,260*1e3,20*1e3)
    #Split into signal and background events
    classes = df['Class']
    dec_vals = df['mBB']
    weights = df['EventWeight']

    y_data = zip(classes, dec_vals, weights)

    events_sb = [[a[1] for a in deepcopy(y_data) if a[0] == 1], [a[1] for a in deepcopy(y_data) if a[0] == 0]]
    weights_sb = [[a[2] for a in deepcopy(y_data) if a[0] == 1], [a[2] for a in deepcopy(y_data) if a[0] == 0]]

    #plots histogram with optimised bins and counts number of signal and background events in each bin
    plt.ioff()
    counts_sb = plt.hist(events_sb,
                         bins=bins,
                         weights=weights_sb)[0]
    plt.close()
    plt.ion()

    # Reverse the counts before calculating.
    # Zip up S, B, DS and DB per bin.
    s_stack = counts_sb[0][::-1]   #counts height of signal in each bin from +1 to -1
    b_stack = counts_sb[1][::-1]    #counts height of bkground in each bin from +1 to -1


    for s, b in zip(s_stack, b_stack): #iterates through every bin
        this_sens = 2 * ((s + b) * math.log(1 + s / b) - s) #calcs sensivity for each bin

        if not math.isnan(this_sens):   #unless bin empty add this_sense to sens_sq total (sums each bin sensitivity)
            sens_sq += this_sens


    # Sqrt operations and error equation balancing.
    sens = math.sqrt(sens_sq)

    return sens



# def sensitivity_bdt(df):
#     """Calculate sensitivity from dataframe with error"""
#
#     # Initialise sensitivity and error.
#     sens_sq = 0
#     bins = 20
#
#     #Split into signal and background events
#     classes = df['Class']
#     dec_vals = df['decision_value']
#     weights = df['EventWeight']
#
#     y_data = zip(classes, dec_vals, weights)
#
#     events_sb = [[a[1] for a in deepcopy(y_data) if a[0] == 1], [a[1] for a in deepcopy(y_data) if a[0] == 0]]
#     weights_sb = [[a[2] for a in deepcopy(y_data) if a[0] == 1], [a[2] for a in deepcopy(y_data) if a[0] == 0]]
#
#     #plots histogram with optimised bins and counts number of signal and background events in each bin
#     plt.ioff()
#     counts_sb = plt.hist(events_sb,
#                          bins=bins* ,
#                          weights=weights_sb)[0]
#     plt.close()
#     plt.ion()
#
#     # Reverse the counts before calculating.
#     # Zip up S, B, DS and DB per bin.
#     s_stack = counts_sb[0][::-1]   #counts height of signal in each bin from +1 to -1
#     b_stack = counts_sb[1][::-1]    #counts height of bkground in each bin from +1 to -1
#
#
#     for s, b in zip(s_stack, b_stack): #iterates through every bin
#         this_sens = 2 * ((s + b) * math.log(1 + s / b) - s) #calcs sensivity for each bin
#         if not math.isnan(this_sens):   #unless bin empty add this_sense to sens_sq total (sums each bin sensitivity)
#             sens_sq += this_sens
#
#
#     # Sqrt operations and error equation balancing.
#     sens = math.sqrt(sens_sq)
#
#     return sens

#
# def plot_heatmap(y_data,poisson_means):
#
#
#     bins = np.arange(min(poisson_means),max(poisson_means)+7,1)
#
#     y_data_binned = []
#     for data in y_data:
#
#         y_data_binned.append(np.histogram(data,bins = bins)[0])
#
#     y_data_binned = np.matrix(np.flip(y_data_binned,axis=1))
#     df = pd.DataFrame(y_data_binned)
#     df = df.set_index((means))
#     bins = np.flip(bins,axis=0)
#     bins = bins[1:]
#
#     df = df.T
#     df = df.set_index(bins)
#
#     fig, ax = plt.subplots()
#     fig.set_size_inches(20,8)
#     xticks = np.arange(min(poisson_means),max(poisson_means)+1)
#
#     sns.heatmap(df,ax = ax, cmap="Oranges",xticklabels = xticks)
#     ax.set(xlabel='Poisson Mean', ylabel='N Seen')
#     xlim = ax.get_xlim()
#     ax.set_xticks(np.linspace(xlim[0],xlim[1],max(poisson_means)- min(poisson_means)));
#
#
#     return df
#

def mean_std_sensitivity(sensitivities, drop=1):
    '''
    Takes the provided sensitities, and calculates the mean and standard
    deviation, excluding 'drop' elements from the start and end. I.e, removes any 
    possible outliers

    Params:
        sensitivies - list of floats: Output model sensitivities
        drop - number of largest/smallest elements to drop
    
    Returns:
        mean, std - floats
            Mean and std of sensitivies excluding outliers
    '''

    sensitivities.sort()
    if drop > 0:
        sensitivities = sensitivities[drop:-drop]
    
    return np.mean(sensitivities), np.std(sensitivities)


def get_row(df,poisson_means,row_number):
    row = []
    for i in poisson_means:

        row+=[i]*df.loc[row_number][i]

    return row

def plot_histories(histories):

    if not isinstance(histories, list):
        histories = [histories]
    
    fig, ax = plt.subplots(1,2,figsize=(15,5))
    main_lines = []
    main_labels = []
    for i, hist in enumerate(histories):
        p = ax[0].plot(hist.history['loss'], label=f'Model {i}')
        
        col = p[0].get_color()
        main_labels.append(f"Model {i}")
        main_lines.append(Line2D([], [], color=col, lw=2, ls='solid'))

        ax[0].plot(hist.history['val_loss'], c=col, ls='dotted', )
        ax[0].set_title("Loss")
        ax[0].set_ylabel("Binary Cross Entropy Loss")
        ax[0].set_xlabel("Epoch")
        # ax[0].legend()
        main_lines.append(Line2D([], [], color=col, lw=2, ls='solid'))
        ax[1].plot(hist.history['accuracy'], c=col, label='train')
        ax[1].plot(hist.history['val_accuracy'], ls='dotted', c=col, )
        ax[1].set_title("Accuracy")
        ax[1].set_ylabel("Accuracy")
        ax[1].set_xlabel("Epoch")
        # ax[1].legend()

    custom_lines = [Line2D([0], [0], color='black', lw=2, ls='solid'),
                Line2D([0], [0], color='black', lw=2, ls='dotted'),
                ]

    plt.sca(ax[0])
    lin_leg = plt.legend(custom_lines, ['Training', 'Validation'], loc='upper center')
    plt.gca().add_artist(lin_leg)
    
    # axes[0,i].set_ylim(ylim[0], 1.4*ylim[1])
    # main_lines.append(Line2D([], [], color='black', lw=2, ls='--'))
    plt.legend(main_lines, main_labels, loc='upper right')
    plt.show()


def sensitivity_NN(df):
    """Calculate sensitivity from dataframe with error"""

    bins, bin_sums_w2_s, bin_sums_w2_b = trafoD_with_error(df, 1000)

    # Initialise sensitivity and error.
    sens_sq = 0
    error_sq = 0

    #Split into signal and background events
    classes = df['Class']
    dec_vals = df['decision_value']
    weights = df['EventWeight']

    y_data = zip(classes, dec_vals, weights)

    events_sb = [[a[1] for a in deepcopy(y_data) if a[0] == 1], [a[1] for a in deepcopy(y_data) if a[0] == 0]]
    weights_sb = [[a[2] for a in deepcopy(y_data) if a[0] == 1], [a[2] for a in deepcopy(y_data) if a[0] == 0]]

    #plots histogram with optimised bins and counts number of signal and background events in each bin
    plt.ioff()
    counts_sb = plt.hist(events_sb,
                         bins=bins,
                         weights=weights_sb)[0]
    plt.close()
    plt.ion()

    # Reverse the counts before calculating.
    # Zip up S, B, DS and DB per bin.
    s_stack = counts_sb[0][::-1]   #counts height of signal in each bin from +1 to -1
    b_stack = counts_sb[1][::-1]    #counts height of bkground in each bin from +1 to -1
    ds_sq_stack = bin_sums_w2_s[::-1]
    db_sq_stack = bin_sums_w2_b[::-1]

    for s, b, ds_sq, db_sq in zip(s_stack, b_stack, ds_sq_stack, db_sq_stack): #iterates through every bin
        if b != 0:
            this_sens = 2 * ((s + b) * math.log(1 + s / b) - s) #calcs sensivity for each bin
            this_dsens_ds = 2 * math.log(1 + s/b)
            this_dsens_db = 2 * (math.log(1 + s/b) - s/b)
            this_error = (this_dsens_ds ** 2) * ds_sq + (this_dsens_db ** 2) * db_sq
            if not math.isnan(this_sens):   #unless bin empty add this_sense to sens_sq total (sums each bin sensitivity)
                sens_sq += this_sens
            if not math.isnan(this_error):  #unless bin empty add this_error to error_sq total
                error_sq += this_error

    # Sqrt operations and error equation balancing.
    sens = math.sqrt(sens_sq)
    error = 0.5 * math.sqrt(error_sq/sens_sq)

    return sens, error


def trafoD_with_error(df, initial_bins=1000, z_s=10, z_b=10): #total number of bins = z_s + z_b
    """Output optimised histogram bin widths from a list of events"""

    df = df.sort_values(by='decision_value')

    N_s = sum(df['post_fit_weight']*df['Class'])
    N_b = sum(df['post_fit_weight']*(1-df['Class']))


    # Set up scan parameters.
    scan_points = np.linspace(-1, 1, num=initial_bins).tolist()[1:-1]
    scan_points = scan_points[::-1] #invert list

    # Initialise z and bin list.
    z = 0
    bins = [1.0]
    sum_w2_s = 0
    sum_w2_b = 0
    delta_bins_s = list()
    delta_bins_b = list()

    decision_values_list = df['decision_value'].tolist()
    class_values_list = df['Class'].tolist()
    post_fit_weights_values_list = df['post_fit_weight'].tolist()

    try:
        # Iterate over bin low edges in scan.
        for p in scan_points:
            # Initialise freq count for this bin
            sig_bin = 0
            back_bin = 0

            # Current bin loop.
            # Remember, events are in descending DV order.
            while True:
                """ This loop sums the post_fit_weight and p.f.w squared of signal and of background events contained in each of the initial bins"""
                # End algo if no events left - update z and then IndexError

                if not decision_values_list: #if not empty (NEVER CALLS THIS CODE)
                    z += z_s * sig_bin / N_s + z_b * back_bin / N_b
                    if z > 1:
                        bins.insert(0, p)
                        delta_bins_s.insert(0, sum_w2_s)
                        delta_bins_b.insert(0, sum_w2_b)
                    raise IndexError


                # Break if DV not in bin. (i.e when finished scanning over each of the inital bins)
                if decision_values_list[-1] < p:  #negative index counts from the right (i.e last object)
                    break

                # Pop the event.
                decison_val = decision_values_list.pop()
                class_val = class_values_list.pop()
                post_fit_weight_val = post_fit_weights_values_list.pop()

                # Add freq to S/B count, and the square to sums of w2.
                if class_val == 1:
                    sig_bin += post_fit_weight_val
                    sum_w2_s += post_fit_weight_val ** 2
                else:
                    back_bin += post_fit_weight_val
                    sum_w2_b += post_fit_weight_val ** 2

            # Update z for current bin.
            z += z_s * sig_bin / N_s + z_b * back_bin / N_b   #10*(% of total signal + # of total background)

            # Reset z and update bin
            if z > 1:
                bins.insert(0, p)
                z = 0

                # Update sum_w2 for this bin.
                delta_bins_s.insert(0, sum_w2_s)
                delta_bins_b.insert(0, sum_w2_b)
                sum_w2_s = 0 #not sure why this is at the end and sig_bin/back_bin reset at the beginning
                sum_w2_b = 0

    except IndexError:
        rewje = 0

    finally:
        bins.insert(0,-1.0)
        delta_bins_s.insert(0, sum_w2_s)  #sum of signal event weights^2 for each bin
        delta_bins_b.insert(0, sum_w2_b)  #sum of background event weights^2 for each bin
        # print("TrafoD",len(bins))
        return bins, delta_bins_s, delta_bins_b

