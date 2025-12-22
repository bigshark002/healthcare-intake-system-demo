import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigatewayv2';
import * as apigatewayIntegrations from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';
import * as path from 'path';

export class ComputeStack extends cdk.Stack {
  public readonly lambdaFunction: lambda.Function;
  public readonly logGroup: logs.LogGroup;
  public readonly apiEndpoint: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Log Group with retention
    this.logGroup = new logs.LogGroup(this, 'LambdaLogGroup', {
      logGroupName: '/aws/lambda/healthcare-mas',
      retention: logs.RetentionDays.TWO_WEEKS,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // IAM Role for Lambda - USANDO TU PATRÓN
    const lambdaRole = new iam.Role(this, 'LambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Role for Healthcare MAS Lambda function',
    });

    // Bedrock permissions - ADAPTANDO TU CÓDIGO
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream',
      ],
      resources: ['*'], // Scope down in production
    }));

    // CloudWatch permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'logs:CreateLogGroup',
        'logs:CreateLogStream',
        'logs:PutLogEvents',
      ],
      resources: [this.logGroup.logGroupArn],
    }));

    // X-Ray permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'xray:PutTraceSegments',
        'xray:PutTelemetryRecords',
      ],
      resources: ['*'],
    }));

    // CloudWatch Metrics permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['cloudwatch:PutMetricData'],
      resources: ['*'],
    }));

    // Lambda Function - BASADO EN TU ESTRUCTURA
    this.lambdaFunction = new lambda.Function(this, 'HealthcareMASFunction', {
      functionName: 'healthcare-mas',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'app.handler.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../../'), {
        bundling: {
          image: lambda.Runtime.PYTHON_3_12.bundlingImage,
          command: [
            'bash', '-c',
            'pip install -r requirements.txt -t /asset-output && cp -r app /asset-output/',
          ],
        },
      }),
      role: lambdaRole,
      timeout: cdk.Duration.seconds(60),
      memorySize: 512,
      environment: {
        POWERTOOLS_SERVICE_NAME: 'healthcare-mas',
        POWERTOOLS_METRICS_NAMESPACE: 'HealthcareMAS',
        LOG_LEVEL: 'INFO',
        HEALTHCARE_MAS_CONFIDENCE_THRESHOLD: '0.70',
        HEALTHCARE_MAS_HUMAN_REVIEW_URGENCY_THRESHOLD: '2',
        HEALTHCARE_MAS_ENABLE_FALLBACK: 'true',
      },
      tracing: lambda.Tracing.ACTIVE,
      logGroup: this.logGroup,
    });

    // HTTP API Gateway
    const httpApi = new apigateway.HttpApi(this, 'HealthcareMASApi', {
      apiName: 'healthcare-mas-api',
      description: 'Healthcare Multi-Agent System API',
      corsPreflight: {
        allowOrigins: ['*'],
        allowMethods: [apigateway.CorsHttpMethod.POST],
        allowHeaders: ['Content-Type'],
      },
    });

    // Add route
    httpApi.addRoutes({
      path: '/process',
      methods: [apigateway.HttpMethod.POST],
      integration: new apigatewayIntegrations.HttpLambdaIntegration(
        'LambdaIntegration',
        this.lambdaFunction
      ),
    });

    this.apiEndpoint = httpApi.apiEndpoint;

    // Outputs
    new cdk.CfnOutput(this, 'ApiEndpoint', {
      value: `${httpApi.apiEndpoint}/process`,
      description: 'API Endpoint URL',
    });

    new cdk.CfnOutput(this, 'FunctionArn', {
      value: this.lambdaFunction.functionArn,
      description: 'Lambda Function ARN',
    });
  }
}