import json
import os

import aws_cdk as cdk
import aws_cdk.aws_appconfig as appconfig
import aws_cdk.aws_lambda as _lambda

app = cdk.App()
stack = cdk.Stack(app, "lambda-powertools-feature-flags-demo-stack")

# ==> AppConfig

# AppConfigにアプリケーションを追加
config_app = appconfig.CfnApplication(
    stack,
    "app",
    name="product-catalogue",
)
# AppConfigに環境を追加
config_env = appconfig.CfnEnvironment(
    stack,
    "env",
    application_id=config_app.ref,
    name="dev-env",
)
# AppConfigにプロファイルを追加
config_profile = appconfig.CfnConfigurationProfile(
    stack,
    "profile",
    application_id=config_app.ref,
    location_uri="hosted",
    name="features",
)

features_config = {
    "premium_features": {
        "default": False,
        "rules": {
            "customer tier equals premium": {
                "when_match": True,
                "conditions": [{"action": "EQUALS", "key": "tier", "value": "premium"}],
            }
        },
    },
    "ten_percent_off_campaign": {"default": True},
}
hosted_cfg_version = appconfig.CfnHostedConfigurationVersion(
    stack,
    "version",
    application_id=config_app.ref,
    configuration_profile_id=config_profile.ref,
    content=json.dumps(features_config),
    content_type="application/json",
)
app_config_deployment = appconfig.CfnDeployment(
    stack,
    id="deploy",
    application_id=config_app.ref,
    configuration_profile_id=config_profile.ref,
    configuration_version=hosted_cfg_version.ref,
    deployment_strategy_id="AppConfig.AllAtOnce",
    environment_id=config_env.ref,
)

# ==> lambda

powertools_layer = _lambda.LayerVersion.from_layer_version_arn(
    stack,
    "lambda-powertools-layer",
    f"arn:aws:lambda:{os.getenv('CDK_DEFAULT_REGION')}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:16",
)
_lambda.Function(
    stack,
    "function",
    runtime=_lambda.Runtime.PYTHON_3_9,
    architecture=_lambda.Architecture.ARM_64,
    code=_lambda.Code.from_asset("runtime"),
    handler="hooks.pre_hook_handler",
    layers=[powertools_layer],
)

app.synth()
