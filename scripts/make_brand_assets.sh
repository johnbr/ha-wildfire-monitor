#!/bin/sh
# Render the brand icon Home Assistant and HACS show for this integration.
# HACS's `brands` check looks for custom_components/<domain>/brand/icon.png,
# and Home Assistant picks up icon@2x.png for high-density screens.
#
# Needs rsvg-convert (librsvg). The artwork is drawn by hand in
# scripts/brand-icon.svg rather than taken from an icon set, so it carries no
# third-party license.
set -eu
cd "$(dirname "$0")/.."
out=custom_components/wildfire_monitor/brand
rsvg-convert -w 256 -h 256 scripts/brand-icon.svg -o "$out/icon.png"
rsvg-convert -w 512 -h 512 scripts/brand-icon.svg -o "$out/icon@2x.png"
