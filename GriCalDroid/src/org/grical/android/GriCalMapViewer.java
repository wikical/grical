/*
 * Copyright 2011 Thomas Fricke, grical.org
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
package org.grical.android;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.mapsforge.android.maps.ArrayItemizedOverlay;
import org.mapsforge.android.maps.GeoPoint;
import org.mapsforge.android.maps.OverlayItem;
import org.mapsforge.applications.android.advancedmapviewer.AdvancedMapViewer;

import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.util.Log;

/**
 * Extension of the {@link AdvancedMapViewer} using GridCalendar to show upcoming events on the
 * map.
 */
public class GriCalMapViewer extends AdvancedMapViewer {
	private static final String TAG = "GriCalMapViewer";

	private static boolean hasNotNull(final JSONObject jsonobject, final String name) {
		try {
			return jsonobject.has(name) && jsonobject.get(name) != null;
		} catch (JSONException e) {
			return false;
		}
	}

	@Override
	protected void createOverlay() {
		// create the default marker for overlay items
		Drawable itemDefaultMarker = getResources().getDrawable(R.drawable.marker_red);

		// create an individual marker for an overlay item
		Drawable itemMarker = getResources().getDrawable(R.drawable.marker_green);

		ArrayItemizedOverlay itemizedOverlay = new ArrayItemizedOverlay(itemDefaultMarker, this);
		final EventRequest eventRequest = new EventRequest(this.mapView);
		final JSONArray array = eventRequest.retrieveObjects();
		final int length = array.length();
		for (int i = 0; i < length; i++) {
			try {
				final JSONObject fields = ((JSONObject) array.get(i)).getJSONObject("fields");
				if (hasNotNull(fields, "coordinates") && hasNotNull(fields, "title")
						&& hasNotNull(fields, "upcoming") && hasNotNull(fields, "tags")) {
					final String coord = fields.get("coordinates").toString();
					final String title = fields.get("title").toString();
					final String upcoming = fields.get("upcoming").toString();
					final String tags = fields.getString("tags");

					Log.e(TAG, coord);
					final String cleancoord = coord.replace("POINT (", "").replace(")", "");
					Log.e(TAG, cleancoord);
					final String latlong[] = cleancoord.split(" ");
					if (latlong.length == 2) {
						final GeoPoint geopoint = new GeoPoint(Double.parseDouble(latlong[1]),
								Double.parseDouble(latlong[0]));
						Log.d(TAG, title + " " + geopoint.toString() + " " + upcoming);

						OverlayItem item = new OverlayItem(geopoint, title + " " + upcoming,
								tags);
						itemizedOverlay.addItem(item);
					} else {
						Log.e(TAG, "uncomplete coord\n" + fields.toString());
					}
				} else {
					Log.e(TAG, "uncomplete fields\n" + fields.toString());
				}

			} catch (JSONException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}

		}
		// add all overlays to the MapView
		this.mapView.getOverlays().add(itemizedOverlay);
	}

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		createOverlay();

	}

}