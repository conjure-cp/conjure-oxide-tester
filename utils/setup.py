from utils import *
import json

with Path("settings.json").open("r", encoding="utf-8") as f:
    settings = json.load(f)

runner_commands = dict(settings["runner_commands"])
print(runner_commands)


def form_df():

    # Initial data
    essences = find_essence_files(".")
    data = {
        "models": essences
    }

    for runner in runner_commands.keys():
        data[runner] = [-2.0 for i in essences]
        print(data[runner])

    print(data)

    df = pd.DataFrame(data)

    df.to_csv(settings["outfile"], index=False)


if __name__ == "__main__":
    form_df()