#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { ComputeStack } from '../lib/stacks/compute-stack';
import { ObservabilityStack } from '../lib/stacks/observability-stack';

const app = new cdk.App();

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
};

// Compute stack (Lambda + API Gateway)
const computeStack = new ComputeStack(app, 'HealthcareMAS-Compute', {
  env,
  description: 'Healthcare Multi-Agent System - Compute Resources',
});

// Observability stack (Dashboard + Alarms)
const observabilityStack = new ObservabilityStack(app, 'HealthcareMAS-Observability', {
  env,
  description: 'Healthcare Multi-Agent System - Observability',
  lambdaFunction: computeStack.lambdaFunction,
  logGroup: computeStack.logGroup,
});

observabilityStack.addDependency(computeStack);

// Tags
cdk.Tags.of(app).add('Project', 'HealthcareMAS');
cdk.Tags.of(app).add('Environment', 'development');