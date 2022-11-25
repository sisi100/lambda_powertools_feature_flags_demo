import os

from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags

feature_flags = FeatureFlags(
    store=AppConfigStore(
        application=os.getenv("APPLICATION_NAME"),
        environment=os.getenv("ENV_NAME"),
        name=os.getenv("PROFILE_NAME"),
    )
)


def handler(event, context):
    flg = feature_flags.evaluate(
        name="dynamic_hogehoge_flags",
        context={"user_id": event["user_id"]},
        default=False,
    )
    print(f"フラグは{str(flg)}です")
    return
