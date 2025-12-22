import * as cdk from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as cw_actions from 'aws-cdk-lib/aws-cloudwatch-actions';
import { Construct } from 'constructs';

interface ObservabilityStackProps extends cdk.StackProps {
  lambdaFunction: lambda.Function;
  logGroup: logs.LogGroup;
}

export class ObservabilityStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ObservabilityStackProps) {
    super(scope, id, props);

    const { lambdaFunction, logGroup } = props;
    const namespace = 'HealthcareMAS';

    // SNS Topic for Alarms
    const alarmTopic = new sns.Topic(this, 'AlarmTopic', {
      topicName: 'healthcare-mas-alarms',
      displayName: 'Healthcare MAS Alerts',
    });

    // ========================================
    // METRICS
    // ========================================

    // Case Duration metric
    const caseDurationMetric = new cloudwatch.Metric({
      namespace,
      metricName: 'CaseDuration',
      statistic: 'avg',
      period: cdk.Duration.minutes(5),
    });

    // Error rate metric
    const errorMetric = new cloudwatch.Metric({
      namespace,
      metricName: 'Errors',
      statistic: 'sum',
      period: cdk.Duration.minutes(5),
    });

    // Human review required metric
    const humanReviewMetric = new cloudwatch.Metric({
      namespace,
      metricName: 'HumanReviewRequired',
      statistic: 'sum',
      period: cdk.Duration.minutes(5),
    });

    // Agent-specific metrics
    const createAgentMetric = (agentName: string, metricName: string) => 
      new cloudwatch.Metric({
        namespace,
        metricName,
        dimensionsMap: { agent: agentName },
        statistic: 'avg',
        period: cdk.Duration.minutes(5),
      });

    // ========================================
    // ALARMS
    // ========================================

    // High Error Rate Alarm
    const errorAlarm = new cloudwatch.Alarm(this, 'HighErrorRateAlarm', {
      alarmName: 'healthcare-mas-high-error-rate',
      alarmDescription: 'Error rate exceeds threshold',
      metric: errorMetric,
      threshold: 5,
      evaluationPeriods: 2,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    errorAlarm.addAlarmAction(new cw_actions.SnsAction(alarmTopic));

    // High Latency Alarm
    const latencyAlarm = new cloudwatch.Alarm(this, 'HighLatencyAlarm', {
      alarmName: 'healthcare-mas-high-latency',
      alarmDescription: 'Case processing latency exceeds 10 seconds',
      metric: caseDurationMetric,
      threshold: 10000, // 10 seconds in ms
      evaluationPeriods: 3,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    latencyAlarm.addAlarmAction(new cw_actions.SnsAction(alarmTopic));

    // Low Confidence Alarm
    const confidenceAlarm = new cloudwatch.Alarm(this, 'LowConfidenceAlarm', {
      alarmName: 'healthcare-mas-low-confidence',
      alarmDescription: 'Average confidence score is low',
      metric: new cloudwatch.Metric({
        namespace,
        metricName: 'Confidence',
        statistic: 'avg',
        period: cdk.Duration.minutes(10),
      }),
      threshold: 0.7,
      evaluationPeriods: 2,
      comparisonOperator: cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    confidenceAlarm.addAlarmAction(new cw_actions.SnsAction(alarmTopic));

    // Lambda Errors Alarm
    const lambdaErrorAlarm = new cloudwatch.Alarm(this, 'LambdaErrorAlarm', {
      alarmName: 'healthcare-mas-lambda-errors',
      alarmDescription: 'Lambda function errors detected',
      metric: lambdaFunction.metricErrors({
        period: cdk.Duration.minutes(5),
      }),
      threshold: 1,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    lambdaErrorAlarm.addAlarmAction(new cw_actions.SnsAction(alarmTopic));

    // ========================================
    // DASHBOARD
    // ========================================

    const dashboard = new cloudwatch.Dashboard(this, 'HealthcareMAS-Dashboard', {
      dashboardName: 'HealthcareMAS-Dashboard',
    });

    // Row 1: Overview
    dashboard.addWidgets(
      new cloudwatch.TextWidget({
        markdown: '# Healthcare Multi-Agent System\n\nReal-time monitoring of the intake coordination system.',
        width: 24,
        height: 2,
      })
    );

    // Row 2: Key Metrics
    dashboard.addWidgets(
      new cloudwatch.SingleValueWidget({
        title: 'Cases Processed (1h)',
        metrics: [new cloudwatch.Metric({
          namespace,
          metricName: 'Success',
          statistic: 'sum',
          period: cdk.Duration.hours(1),
        })],
        width: 6,
        height: 4,
      }),
      new cloudwatch.SingleValueWidget({
        title: 'Error Rate',
        metrics: [errorMetric],
        width: 6,
        height: 4,
      }),
      new cloudwatch.SingleValueWidget({
        title: 'Avg Case Duration',
        metrics: [caseDurationMetric],
        width: 6,
        height: 4,
      }),
      new cloudwatch.SingleValueWidget({
        title: 'Human Reviews Required',
        metrics: [humanReviewMetric],
        width: 6,
        height: 4,
      })
    );

    // Row 3: Latency by Agent
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Agent Latency (p50, p99)',
        left: [
          createAgentMetric('intake', 'Duration'),
          createAgentMetric('triage', 'Duration'),
          createAgentMetric('routing', 'Duration'),
        ],
        width: 12,
        height: 6,
      }),
      new cloudwatch.GraphWidget({
        title: 'Confidence Scores by Agent',
        left: [
          createAgentMetric('intake', 'Confidence'),
          createAgentMetric('triage', 'Confidence'),
          createAgentMetric('routing', 'Confidence'),
        ],
        width: 12,
        height: 6,
      })
    );

    // Row 4: Urgency and Cost
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Urgency Level Distribution',
        left: [new cloudwatch.Metric({
          namespace,
          metricName: 'UrgencyLevel',
          statistic: 'avg',
          period: cdk.Duration.minutes(5),
        })],
        width: 12,
        height: 6,
      }),
      new cloudwatch.GraphWidget({
        title: 'Estimated Cost (USD)',
        left: [new cloudwatch.Metric({
          namespace,
          metricName: 'EstimatedCostUSD',
          statistic: 'sum',
          period: cdk.Duration.hours(1),
        })],
        width: 12,
        height: 6,
      })
    );

    // Row 5: Lambda Metrics
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Lambda Invocations & Errors',
        left: [
          lambdaFunction.metricInvocations({ period: cdk.Duration.minutes(5) }),
          lambdaFunction.metricErrors({ period: cdk.Duration.minutes(5) }),
        ],
        width: 12,
        height: 6,
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda Duration',
        left: [
          lambdaFunction.metricDuration({ statistic: 'avg', period: cdk.Duration.minutes(5) }),
          lambdaFunction.metricDuration({ statistic: 'p99', period: cdk.Duration.minutes(5) }),
        ],
        width: 12,
        height: 6,
      })
    );

    // Row 6: Alarms Status
    dashboard.addWidgets(
      new cloudwatch.AlarmStatusWidget({
        title: 'System Health',
        alarms: [errorAlarm, latencyAlarm, confidenceAlarm, lambdaErrorAlarm],
        width: 24,
        height: 4,
      })
    );

    // Outputs
    new cdk.CfnOutput(this, 'DashboardUrl', {
      value: `https://${this.region}.console.aws.amazon.com/cloudwatch/home?region=${this.region}#dashboards:name=HealthcareMAS-Dashboard`,
      description: 'CloudWatch Dashboard URL',
    });

    new cdk.CfnOutput(this, 'AlarmTopicArn', {
      value: alarmTopic.topicArn,
      description: 'SNS Topic for Alarms',
    });
  }
}