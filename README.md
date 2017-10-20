## AWS Geolambda Task for Converting MODIS, VIIRS, and USGS shapefiles to GeoJSON

This is a Python-based lambda function that converts shapefiles to geojsons. Specifically, it converts the 7-day US (Conterminous and Hawaii) Fire data (375m resolution) via NASA/NOAA VIIRS (Suomi polar orbit) that is posted at: https://earthdata.nasa.gov/earth-observation-data/near-real-time/firms/active-fire-data. 

It also converts the GeoMAC/USGS fire name data posted at: https://rmgsc.cr.usgs.gov/outgoing/GeoMAC/current_year_fire_data/current_year_all_states/

The creation of this task was prompted by a note on Burrito Justice's [sonoma-napa-fire-map-viirs](https://github.com/burritojustice/sonoma-napa-fire-map-viirs) about the manual conversion of the daily passes.

To make this all work, this tasks uses Development Seed's excellent [Geolamdbda Docker images](https://developmentseed.org/blog/2017/08/17/geolambdas/) for buindling core geo liibraries into a deployable package. Their deployment write-up covers how this lambda is packaged and built.

### Building and Deploying

1. Build the base image that is referenced in the `docker-compose.yml`:

   `docker build -t modisviirs ./`

2. Set up an s3 bucket and update the name referenced in `lambda/lambda_handler.py`

3. Package the lambda for deployment:

   `docker-compose run package`

4. Deploy to AWS:

   `aws lambda update-function-code --function-name modis-viirs-convert --zip-file fileb://lambda-deploy.zip`

   Note: As discussed in the Development Seed docs, this presumes that you've already set up your function on AWS. Since we are making a number of network calls and dealing with File I/O, we need to bump up the timeout limit before we can run this; 2 minutes was enough.

 5. Create a test event in the AWS Lambda dashboard. I used the `Hello World` template. We don't do any processing with the event payload, so you can stick whatever you want in the payload space. Once you've configured your test, click the `Test` button and wait for the output to appear in your s3 bucket.

 6. Configure a CloudWatch event to execute the conversion script on a time table. Create a CloudWatch Rule and select your lambda function as the target. You can either run it on fixed intervals or pass in a more specific CRON style schedule.

 