# [MusicChartsAI](https://musicchartsai.com)

## Apps

- Starter public site ready to be customized to showcase important information and acquire interest
- Dashboard private site, showing customer facing aggregated data
- Admin dashboard for preparing the platform, operate on data, trigger and monitor the data fetching tasks

- Management commands to start the data sync
- Background cron tasks to keep data in sync

The dashboard is crafted on top of **[Rocket](https://app-generator.dev/product/adminlte/)** design, styled with Tailwind/Flowbite. The product is designed to deliver the best possible user experience with highly customizable feature-rich pages.
The admin is using the jazzymin django admin theme.

## Tech stack

- Python 3.13
- Node 22.0.0
- Django 5.2
- Webpack
- Tailwind
- ApexCharts

## Features

- Django admin customizations
- Tailwind dashboard
- Soundcharts API integration
- ACRCloud API integration
- Background tasks execution for data sync

- Dynamic Tables - read [docs](https://app-generator.dev/docs/developer-tools/dynamic-datatables.html)
- Dynamic API - read [docs](https://app-generator.dev/docs/developer-tools/dynamic-api.html)
- Apex Charts

- Session-based Authentication, Password recovery
- DB Persistence: SQLite (default), can be used with MySql, PgSql
- Docker, CI/CD for Render

<br />

## Deploy LIVE

> One-click deploy (requires to have an account).

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

<br /> 

> On premise deploy (requires a linux server with ssh access)
- Ensure pyenv build requirements are met:
https://github.com/pyenv/pyenv/wiki#suggested-build-environment
    `> sudo apt update; sudo apt install make build-essential libssl-dev zlib1g-dev \`
    `libbz2-dev libreadline-dev libsqlite3-dev curl git \`
    `libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev`
- Ensure the correct python 3.13 version is installed, otherwise `> pyenv install 3.13`
- Create a virtualenv and install deps from requirements.txt `python -m virtualenv venv`

<br />
