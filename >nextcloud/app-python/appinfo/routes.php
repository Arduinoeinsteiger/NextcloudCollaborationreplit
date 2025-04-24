<?php

declare(strict_types=1);

/**
 * @copyright Copyright (c) 2023 SwissAirDry Team
 *
 * @author SwissAirDry Team
 *
 * @license AGPL-3.0-or-later
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

return [
    'routes' => [
        // Frontend-Routen
        ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
        ['name' => 'page#dashboard', 'url' => '/dashboard', 'verb' => 'GET'],
        ['name' => 'page#devices', 'url' => '/devices', 'verb' => 'GET'],
        ['name' => 'page#device_detail', 'url' => '/devices/{id}', 'verb' => 'GET'],
        ['name' => 'page#alarms', 'url' => '/alarms', 'verb' => 'GET'],
        ['name' => 'page#settings', 'url' => '/settings', 'verb' => 'GET'],
        
        // API-Routen
        ['name' => 'api#get_status', 'url' => '/api/status', 'verb' => 'GET'],
        ['name' => 'api#get_devices', 'url' => '/api/devices', 'verb' => 'GET'],
        ['name' => 'api#get_device', 'url' => '/api/devices/{id}', 'verb' => 'GET'],
        ['name' => 'api#update_device', 'url' => '/api/devices/{id}', 'verb' => 'PUT'],
        ['name' => 'api#create_device', 'url' => '/api/devices', 'verb' => 'POST'],
        ['name' => 'api#delete_device', 'url' => '/api/devices/{id}', 'verb' => 'DELETE'],
        ['name' => 'api#get_device_telemetry', 'url' => '/api/devices/{id}/telemetry', 'verb' => 'GET'],
        ['name' => 'api#get_alarms', 'url' => '/api/alarms', 'verb' => 'GET'],
        ['name' => 'api#get_alarm', 'url' => '/api/alarms/{id}', 'verb' => 'GET'],
        ['name' => 'api#create_alarm', 'url' => '/api/alarms', 'verb' => 'POST'],
        ['name' => 'api#update_alarm', 'url' => '/api/alarms/{id}', 'verb' => 'PUT'],
        ['name' => 'api#delete_alarm', 'url' => '/api/alarms/{id}', 'verb' => 'DELETE'],
        
        // Webhook-Routen
        ['name' => 'webhook#device', 'url' => '/webhook/device', 'verb' => 'POST'],
        ['name' => 'webhook#alarm', 'url' => '/webhook/alarm', 'verb' => 'POST'],
        
        // MQTT-Proxy
        ['name' => 'mqtt#publish', 'url' => '/mqtt/publish', 'verb' => 'POST'],
        ['name' => 'mqtt#subscribe', 'url' => '/mqtt/subscribe', 'verb' => 'POST'],
        
        // Deck-Integration
        ['name' => 'deck#create_board', 'url' => '/deck/create-board', 'verb' => 'POST'],
        ['name' => 'deck#create_card', 'url' => '/deck/create-card', 'verb' => 'POST'],
        ['name' => 'deck#get_boards', 'url' => '/deck/boards', 'verb' => 'GET'],
        ['name' => 'deck#get_stacks', 'url' => '/deck/boards/{boardId}/stacks', 'verb' => 'GET'],
    ],
];