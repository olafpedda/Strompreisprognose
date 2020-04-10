# Strompreisprognose
Dieses Projekt behandelt die Prognose des Day Ahead-Strompreises für das Marktbegiebt Deutschland/Luxemburg. Für die Prognosen werden Einflussfaktoren wie Wetter, Feiertage und Tageszeit berücksichtigt.

## Einführung
prognose.py berechnet standardmäßig für alle Prognosemethoden (neuronale Netze/statistische Methoden) mit der bisher optimalsten Konfiguration für die neuronalen Netze und statistischen Methoden. 
Die Konfiguration der Netze und weitere Parameter können über die Variablen in prognose.py eingestellt werden. 
Die Ergebnisse eines Zeitschrittes werden in 4 Diagrammen dargestellt. Oben befindet sich dabei die komplette Zeitreihe des Strompreises mit der Prognose des Neuronalen Netzes und der aufsummierten Prognose der einzelnen Zeitreihenkomponenten. In dem untersten Diagramm wird die Referenzprognose des naiven Modells dargestellt. In den anderen drei mittleren Diagrammen sind die Prognosen für die einzelnen Zeitreihenkomponenten dargestellt. In der Legende befindet sich jeweils der mittlere Fehler für diese Prognose. 
## Variablen
normale Variablen:
- `future_target` beschreibt die Länge der Vorhersage.
- `iterations` beschreibt, wie viele Stunden eine "mass predict" durchgeführt werden soll. 
- `step` beschreibt in was für Abständen die einzelnen Prognosen der Massenprognose berechnet werden.
- `epochs` beschreibt die Anzahl an Epochen für den Trainingsprozess.
- `train_complete` und `train_residual` beschreiben, ob ein Netz neu trainiert werden soll (True) oder ein bereits trainiertes Netz geladen werden soll.

Zu den Argument Parametern, die Entscheiden wie lang der Inputzeitraum und die Struktur des Netzes ist, sind jeweils Hilfesätze gegeben, die die Funktion aufklären sollten.

## Daten
Der automatische Download für die Daten ist deaktiviert, sodass bereits heruntergeladene Daten verwendet werden. Um die Daten zu aktualisieren muss der override für `get_new_power_data` und `get_new_weather_data` in **csv_Reader.get_data** auskommentiert werden.

Die Strompreisdaten werden nach der Creative Commonons Lizens CC BY 4.0 von der Bundesnetzagentur | SMARD.de (https://www.smard.de/home/downloadcenter/download_marktdaten) heruntergeladen und unter Daten/price.csv gespeichert.

Die Wetterdaten werden vom deutschen Wetterdienst auf dem Open Data-Server https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/ bereitgestellt und "dürfen entsprechend der "Verordnung zur Festlegung der Nutzungsbestimmungen für die Bereitstellung von Geodaten des Bundes (GeoNutzV) unter Beigabe eines Quellenvermerks ohne Einschränkungen weiterverwendet werden." (https://www.dwd.de/DE/service/copyright/copyright_node.html). Sie werden unter Daten/weather.csv gespeichert
