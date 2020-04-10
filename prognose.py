from __future__ import absolute_import, division, print_function, \
    unicode_literals
from argparse import ArgumentParser
import matplotlib.pyplot as plt
import numpy as np
from pandas.plotting import register_matplotlib_converters
from csv_reader import get_data
from neuralNetPrediction import NeuralNetPrediction
from statisticalPrediction import StatisticalPrediction
import ipykernel  # fix progress bar

register_matplotlib_converters()
future_target = 24
iterations = 168  # amount of predicitons for mass predict
step = 1
epochs = 150
train_complete = False
train_residual = False
train_day_of_week = False
day_of_week_predictions=False
mass_predict_day_of_week=False

# argument parsing for grid search
parser = ArgumentParser()
parser.add_argument("-p", default=72, type=int,
                    help="amount of input timesteps")
parser.add_argument("-l", default=1, type=int,
                    help="additional layers for neural net")
parser.add_argument("-d", default=2, type=int,
                    help="dropout percentage in additional layer")
parser.add_argument("-cp",
                    default=True, type=bool,
                    help="predict complete part of time series")
parser.add_argument("-dp",
                    default=False, type=bool,
                    help=" predict decomposed part of time series")
parser.add_argument("-mp",
                    default=True, type=bool,
                    help="use mass prediction for error calculation")
parser.add_argument("-s",
                    default=0, type=int,
                    help="hour of the day, where the prediciton should start")

args = parser.parse_args()
past_history = args.p
layers = args.l
dropout = args.d
predict_complete = args.cp
predict_decomposed = args.dp
mass_predict_neural = args.mp
test_pred_start_hour = args.s
plot_all = mass_predict_neural == False
test_length = future_target + iterations + 185  # Timesteps for testing.

train_data, test_data = get_data(test_length=test_length,
                                 test_pred_start_hour=test_pred_start_hour,
                                 past_history=past_history)
# test_data.Price.plot()
# plt.show()

dropout_decimal = dropout / 10
print("configuation: ", past_history, layers, dropout)


if day_of_week_predictions :
    complete_nets=[]
    residual_nets = []

    for i in range(7):
        print("initializing net ",i)
        complete_nets.append(NeuralNetPrediction(datacolumn="Price",
                                          train_data=train_data,
                                          test_data=test_data,
                                          future_target=future_target,
                                          past_history=past_history,
                                          epochs=epochs))


        if train_day_of_week:
            print("training net ", i)
            complete_nets[i].initialize_network(dropout=dropout_decimal,
                                               additional_layers=layers)
            complete_nets[i].train_network(
                savename="complete_day_{}".format(i),
                save=True,
                lr_schedule="polynomal",
                power=2)  # lr_schedule="polynomal" oder "step

        else:
            complete_nets[i].load_model(savename="complete_day_{}".format(i))


full_prediciton = None
if predict_complete:
    full_prediciton = NeuralNetPrediction(datacolumn="Price",
                                          train_data=train_data,
                                          test_data=test_data,
                                          future_target=future_target,
                                          past_history=past_history,
                                          epochs=epochs)

    if train_complete:
        full_prediciton.initialize_network(dropout=dropout_decimal,
                                           additional_layers=layers)
        full_prediciton.train_network(savename="trainedLSTM_complete",
                                      save=False,
                                      lr_schedule="polynomal",
                                      power=2)  # lr_schedule="polynomal" oder "step

    else:
        full_prediciton.load_model(savename="trainedLSTM_complete")

    if mass_predict_neural:
        full_prediciton.mass_predict(iterations=iterations,
                                     filename="complete",
                                     past_history=past_history,
                                     layers=layers,
                                     step=step,
                                     write_to_File=False,
                                     use_day_model=False)
        full_prediciton.mass_predict(iterations=iterations,
                                     filename="day_model",
                                     past_history=past_history,
                                     layers=layers,
                                     step=step,
                                     write_to_File=False,
                                     use_day_model=True)

    else:
        full_prediciton.predict(offset=0,use_day_model=True)
        plt.plot(full_prediciton.pred,label="day_model, Error:{}".format(full_prediciton.error))
        full_prediciton.predict(offset=0,use_day_model=False)
        plt.plot(full_prediciton.pred,
                 label="complete_model, Error:{}".format(
                     full_prediciton.error))
        plt.plot(full_prediciton.truth.index,full_prediciton.truth,label="Truth")
        plt.legend()
        plt.show()



res_prediction = None
seasonal_pred = None
i = 0
decomp_error = 0
sum_pred = 0
if predict_decomposed:
    # Residual
    res_prediction = NeuralNetPrediction(datacolumn="Remainder",
                                         train_data=train_data,
                                         test_data=test_data,
                                         future_target=future_target,
                                         past_history=past_history,
                                         epochs=epochs)

    if train_residual:
        res_prediction.initialize_network(dropout=dropout_decimal,
                                          additional_layers=layers)
        res_prediction.train_network(savename="trainedLSTM_resid",
                                     save=False,
                                     lr_schedule="polynomal",
                                     power=2)
        # lr_schedule="polynomal" oder "step
    else:
        res_prediction.load_model(savename="trainedLSTM_resid")

    if mass_predict_neural:
        res_prediction.mass_predict(iterations=iterations,
                                    filename="residual",
                                    past_history=past_history,
                                    layers=layers,
                                    step=step,
                                    write_to_File=False)
    else:
        # Remainder
        res_prediction.predict(offset=i)
        sum_pred = res_prediction.pred.copy()

        # Seasonal
        seasonal_pred = StatisticalPrediction(data=test_data,
                                              future_target=future_target,
                                              offset=i,
                                              neural_past_history=past_history,
                                              component="Seasonal")
        seasonal_pred.predict("AutoReg")
        sum_pred += seasonal_pred.pred

        # Trend
        trend_pred = StatisticalPrediction(data=test_data,
                                           future_target=future_target,
                                           offset=i,
                                           neural_past_history=past_history,
                                           component="Trend")
        trend_pred.predict("AutoReg")
        sum_pred += trend_pred.pred

        # add error

        decomp_error += np.around(np.sqrt(np.mean(np.square(
            test_data["Price"].iloc[
            past_history + i: past_history + i + future_target] - sum_pred))),
            2)
        i += 1
    # with open('Results/residual_results.csv', 'a', newline='') as fd:
    #     writer = csv.writer(fd)
    #     writer.writerow([learning_rate, res_prediction.error,
    #                      res_prediction.single_errors.tolist()])



naive_complete_pred = StatisticalPrediction(data=test_data,
                                            future_target=future_target,
                                            offset=0,
                                            neural_past_history=past_history,
                                            component="Price")
naive_complete_pred.predict(method="naive")

# decomp_error /= (i + 1)
if mass_predict_neural == False and predict_complete ==True and predict_decomposed==True:
    fig, ax = plt.subplots(5, 1, sharex=True, figsize=(10.0, 10.0))  #

    timeframe = slice(i - 1 + past_history,
                      past_history + future_target + i - 1)
    index = test_data.iloc[timeframe].index
    ax[0].plot(index, test_data["Price"].iloc[timeframe],
               label="Truth")
    ax[1].plot(index, test_data["Remainder"].iloc[timeframe],
               label="Truth")
    ax[2].plot(index, test_data["Seasonal"].iloc[timeframe],
               label='truth')
    ax[3].plot(index, test_data["Trend"].iloc[timeframe],
               label='truth')
    ax[4].plot(index, naive_complete_pred.truth,
               label="Truth")

    ax[0].plot(index, sum_pred,
               label='decomposed; RMSE : {}'.format(
                   decomp_error))
    ax[0].plot(index, full_prediciton.pred,
               label='complete; RMSE: {}'.format(
                   full_prediciton.error))

    ax[1].plot(index, res_prediction.pred,
               label='Remainder prediciton ; RMSE: '
                     '{}'.format(
                   res_prediction.error))
    ax[2].plot(index, seasonal_pred.pred,
               label="prediction ; Error: {}".format(
                   seasonal_pred.error))
    ax[3].plot(index, trend_pred.pred,
               label="prediction ; Error: {}".format(
                   trend_pred.error))
    ax[4].plot(index, naive_complete_pred.pred,
             label="prediction; RMSE: {}".format(
                 naive_complete_pred.error))

    ax[0].set_ylabel("Komplett")
    ax[1].set_ylabel("Remainder")
    ax[2].set_ylabel("Seasonal")
    ax[3].set_ylabel("Trend")
    ax[4].set_ylabel("Naive Prediction")

    ax[0].legend()
    ax[1].legend()
    ax[2].legend()
    ax[3].legend()
    ax[4].legend()
    # Plot the predictions of components and their combination with the
    # corresponding truth

    fig.suptitle("Start: {} Stunden nach Trainingsende des anderen Versuchs".format(test_pred_start_hour))
    plt.savefig("Abbildungen/prediction_{}.png".format(test_pred_start_hour),dpi=300,bbox_inches='tight')
    #plt.show()

