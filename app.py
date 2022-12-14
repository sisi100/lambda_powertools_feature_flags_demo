import json
import os

import aws_cdk as cdk
from aws_cdk import aws_appconfig as appconfig
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda

app = cdk.App()
stack = cdk.Stack(app, "lambda-powertools-feature-flags-demo-stack")

features_config = {
    # ルール付きの動的に変化するフラグだよ
    "dynamic_hogehoge_flags": {
        "default": False,
        "rules": {
            "hoge rule 1": {
                "when_match": True,
                "conditions": [
                    {
                        "action": "EQUALS",
                        "key": "user_id",
                        "value": "hoge",
                    }
                ],
            }
        },
    },
    # (参考)ルールのない静的なフラグ
    "static_hogehoge_flag": {
        "default": False,
    },
}

# ==> AppConfig

# AppConfigにアプリケーションを追加
app_config = appconfig.CfnApplication(stack, "app", name="demo-app")

# AppConfigに環境を追加
config_env = appconfig.CfnEnvironment(stack, "env", application_id=app_config.ref, name="dev")

# AppConfigにプロファイルを追加
config_profile = appconfig.CfnConfigurationProfile(
    stack,
    "profile",
    application_id=app_config.ref,
    location_uri="hosted",
    name="features",
)

# プロファイルに新しいバージョンを追加
hosted_cfg_version = appconfig.CfnHostedConfigurationVersion(
    stack,
    "version",
    application_id=app_config.ref,
    configuration_profile_id=config_profile.ref,
    content=json.dumps(features_config),
    content_type="application/json",
)

# デプロイ戦略を作成
app_config_deployment = appconfig.CfnDeployment(
    stack,
    id="deploy",
    application_id=app_config.ref,
    configuration_profile_id=config_profile.ref,
    configuration_version=hosted_cfg_version.ref,
    environment_id=config_env.ref,
    deployment_strategy_id="AppConfig.AllAtOnce",  # 即時一括反映
)

# ==> lambda

powertools_layer = _lambda.LayerVersion.from_layer_version_arn(
    stack,
    "lambda-powertools-layer",
    f"arn:aws:lambda:{os.getenv('CDK_DEFAULT_REGION')}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:16",
)
function = _lambda.Function(
    stack,
    "function",
    runtime=_lambda.Runtime.PYTHON_3_9,
    architecture=_lambda.Architecture.ARM_64,
    code=_lambda.Code.from_asset("runtime"),
    handler="index.handler",
    layers=[powertools_layer],
    environment={
        "APPLICATION_NAME": app_config.name,
        "ENV_NAME": config_env.name,
        "PROFILE_NAME": config_profile.name,
    },
)
function.add_to_role_policy(
    iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=["appconfig:GetLatestConfiguration", "appconfig:StartConfigurationSession"],
        resources=["*"],
    )
)

app.synth()
