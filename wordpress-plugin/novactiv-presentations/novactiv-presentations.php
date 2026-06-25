<?php
/**
 * Plugin Name: Office Presentations
 * Description: Отдает нормализованные данные объектов Office по REST API для n8n и генератора презентаций.
 * Version: 0.1.0
 * Author: Office
 * Text Domain: office-presentations
 */

if (!defined('ABSPATH')) {
    exit;
}

final class Office_Presentations_Plugin
{
    private const OPTION_API_TOKEN = 'office_presentations_api_token';
    private const META_PRESENTATION_URL = '_office_presentation_url';

    public function __construct()
    {
        add_action('admin_menu', [$this, 'register_settings_page']);
        add_action('admin_init', [$this, 'register_settings']);
        add_action('rest_api_init', [$this, 'register_rest_routes']);
    }

    public function register_settings_page(): void
    {
        add_options_page(
            'Office Presentations',
            'Office Presentations',
            'manage_options',
            'office-presentations',
            [$this, 'render_settings_page']
        );
    }

    public function register_settings(): void
    {
        register_setting('office_presentations', self::OPTION_API_TOKEN, [
            'type' => 'string',
            'sanitize_callback' => 'sanitize_text_field',
            'default' => '',
        ]);
    }

    public function render_settings_page(): void
    {
        if (!current_user_can('manage_options')) {
            return;
        }
        ?>
        <div class="wrap">
            <h1>Office Presentations</h1>
            <form method="post" action="options.php">
                <?php settings_fields('office_presentations'); ?>
                <table class="form-table" role="presentation">
                    <tr>
                        <th scope="row"><label for="<?php echo esc_attr(self::OPTION_API_TOKEN); ?>">API token</label></th>
                        <td>
                            <input class="regular-text" type="password" id="<?php echo esc_attr(self::OPTION_API_TOKEN); ?>" name="<?php echo esc_attr(self::OPTION_API_TOKEN); ?>" value="<?php echo esc_attr($this->api_token()); ?>" autocomplete="new-password">
                            <p class="description">Необязательный токен для закрытого доступа к REST endpoint плагина.</p>
                        </td>
                    </tr>
                </table>
                <?php submit_button('Сохранить'); ?>
            </form>
        </div>
        <?php
    }

    public function register_rest_routes(): void
    {
        register_rest_route('office/v1', '/property/(?P<id>\d+)', [
            'methods' => \WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_property'],
            'permission_callback' => [$this, 'can_read_rest_property'],
            'args' => [
                'id' => [
                    'required' => true,
                    'validate_callback' => static function ($value): bool {
                        return is_numeric($value);
                    },
                ],
            ],
        ]);
    }

    public function can_read_rest_property(\WP_REST_Request $request): bool
    {
        $token = $this->api_token();
        if ($token === '') {
            return true;
        }

        $provided = (string) $request->get_header('x-office-token');
        return hash_equals($token, $provided);
    }

    public function rest_property(\WP_REST_Request $request)
    {
        $post_id = absint($request['id']);
        $post = get_post($post_id);

        if (!$post || $post->post_type !== 'property' || $post->post_status !== 'publish') {
            return new \WP_Error('office_property_not_found', 'Объект не найден.', ['status' => 404]);
        }

        return rest_ensure_response($this->normalize_property($post));
    }

    private function normalize_property(\WP_Post $post): array
    {
        $title = get_the_title($post);
        $content = wp_strip_all_tags((string) apply_filters('the_content', $post->post_content));
        $meta = get_post_meta($post->ID);
        $acf = function_exists('get_fields') ? (array) get_fields($post->ID) : [];
        $flat_meta = $this->flatten_meta($meta);

        $photos = $this->collect_photos($post->ID, $flat_meta);
        $area = $this->first_value($acf, $flat_meta, ['property_area', 'area_m2', 'area', 'square', 'total_area']);
        if ($area === '') {
            $area = $this->match_first($title, '/(\d+(?:[.,]\d+)?)\s*м²/iu');
        }

        $description = $this->first_value($acf, $flat_meta, ['property_description', 'description']);
        if ($description === '') {
            $description = $content;
        }
        $description = trim(preg_replace('/\s+/', ' ', $description));

        return [
            'wordpress_id' => $post->ID,
            'post_type' => $post->post_type,
            'quickdeal_id' => $this->first_value($acf, $flat_meta, ['property_qd_id']),
            'internal_id' => $this->first_value($acf, $flat_meta, ['property_internal_id']),
            'lot_number' => $this->first_value($acf, $flat_meta, ['property_lot_number']),
            'source_url' => get_permalink($post),
            'slug' => $post->post_name,
            'title' => $this->first_value($acf, $flat_meta, ['property_title', 'title']) ?: $title,
            'city' => $this->first_value($acf, $flat_meta, ['property_locality_name', 'city', 'gorod']) ?: 'Новосибирск',
            'address' => $this->first_value($acf, $flat_meta, ['property_full_address', 'property_address', 'address', 'adres', 'location']),
            'district' => $this->first_value($acf, $flat_meta, ['property_district', 'district']),
            'region' => $this->first_value($acf, $flat_meta, ['property_region', 'region']),
            'latitude' => $this->first_value($acf, $flat_meta, ['property_latitude', 'latitude']),
            'longitude' => $this->first_value($acf, $flat_meta, ['property_longitude', 'longitude']),
            'area_m2' => str_replace(',', '.', $area),
            'area_unit' => $this->first_value($acf, $flat_meta, ['property_area_unit', 'area_unit']),
            'living_space' => $this->first_value($acf, $flat_meta, ['property_living_space', 'living_space']),
            'kitchen_space' => $this->first_value($acf, $flat_meta, ['property_kitchen_space', 'kitchen_space']),
            'rooms' => $this->first_value($acf, $flat_meta, ['property_rooms', 'rooms']),
            'floor' => $this->first_value($acf, $flat_meta, ['property_floor', 'floor']),
            'floors_total' => $this->first_value($acf, $flat_meta, ['property_floors_total', 'floors_total']),
            'price' => $this->first_value($acf, $flat_meta, ['property_price', 'price', 'cost', 'rent_price']),
            'currency' => $this->first_value($acf, $flat_meta, ['property_currency', 'currency']) ?: 'RUB',
            'price_period' => $this->first_value($acf, $flat_meta, ['property_price_period', 'price_period']),
            'price_unit' => $this->first_value($acf, $flat_meta, ['property_price_unit', 'price_unit']),
            'commission' => $this->first_value($acf, $flat_meta, ['property_commission', 'commission']),
            'prepayment' => $this->first_value($acf, $flat_meta, ['property_prepayment', 'prepayment']),
            'security_payment' => $this->first_value($acf, $flat_meta, ['property_security_payment', 'security_payment']),
            'deal_type' => $this->detect_deal_type($title . ' ' . $description, $flat_meta),
            'segment' => $this->detect_segment($title . ' ' . $description, $flat_meta),
            'category' => $this->first_value($acf, $flat_meta, ['property_category', 'category']),
            'property_type' => $this->first_value($acf, $flat_meta, ['property_property_type', 'property_type']),
            'commercial_type' => $this->first_value($acf, $flat_meta, ['property_commercial_type', 'commercial_type']),
            'building_type' => $this->first_value($acf, $flat_meta, ['property_building_type', 'property_commercial_building_type', 'building_type']),
            'building_name' => $this->first_value($acf, $flat_meta, ['property_building_name', 'building_name']),
            'renovation' => $this->first_value($acf, $flat_meta, ['property_renovation', 'renovation']),
            'ceiling_height' => $this->first_value($acf, $flat_meta, ['property_ceiling_height', 'ceiling_height']),
            'description' => $description,
            'features' => $this->features_from_text($title . ' ' . $description, $acf, $flat_meta),
            'photos' => $photos,
            'metro' => $this->array_value($flat_meta, 'property_metro'),
            'railway_station' => $this->array_value($flat_meta, 'property_railway_station'),
            'purpose' => $this->array_value($flat_meta, 'property_purpose'),
            'purpose_warehouse' => $this->array_value($flat_meta, 'property_purpose_warehouse'),
            'video_review' => $this->array_value($flat_meta, 'property_video_review'),
            'virtual_tour' => $this->array_value($flat_meta, 'property_virtual_tour'),
            'discount' => $this->array_value($flat_meta, 'property_discount'),
            'manager' => [
                'name' => $this->first_value($acf, $flat_meta, ['property_agent_name', 'agent_name']),
                'phone' => $this->first_value($acf, $flat_meta, ['property_agent_phone_single', 'agent_phone_single']),
                'phones' => $this->array_value($flat_meta, 'property_agent_phone'),
                'whatsapp' => $this->first_value($acf, $flat_meta, ['property_agent_whatsapp_phone', 'agent_whatsapp_phone']),
                'email' => $this->first_value($acf, $flat_meta, ['property_agent_email', 'agent_email']),
                'organization' => $this->first_value($acf, $flat_meta, ['property_agent_organization', 'agent_organization']),
                'photo' => $this->first_value($acf, $flat_meta, ['property_agent_photo', 'agent_photo']),
            ],
            'presentation_url' => (string) get_post_meta($post->ID, self::META_PRESENTATION_URL, true),
            'published_at' => $this->first_value($acf, $flat_meta, ['property_creation_date']) ?: get_post_time(DATE_ATOM, true, $post),
            'updated_at' => $this->first_value($acf, $flat_meta, ['property_last_update_date', 'property_updateAt']) ?: get_post_modified_time(DATE_ATOM, true, $post),
            'taxonomies' => $this->collect_taxonomies($post->ID),
            'acf' => $acf,
            'meta' => $flat_meta,
        ];
    }

    private function collect_photos(int $post_id, array $meta): array
    {
        $photos = [];
        $seen = [];

        $add_url = static function (string $url, string $caption = '', array $attrs = []) use (&$photos, &$seen): void {
            if (!$url || isset($seen[$url])) {
                return;
            }
            $seen[$url] = true;
            $photos[] = array_merge([
                'url' => $url,
                'caption' => wp_strip_all_tags($caption),
            ], $attrs);
        };

        $add_attachment = static function (int $attachment_id) use ($add_url): void {
            $url = wp_get_attachment_image_url($attachment_id, 'full');
            if ($url) {
                $add_url($url, (string) wp_get_attachment_caption($attachment_id));
            }
        };

        foreach (['property_default_image', 'property_house_main_image'] as $key) {
            if (!empty($meta[$key]) && is_string($meta[$key])) {
                $attrs = $key === 'property_default_image' ? ['is_default' => true] : ['is_house_main' => true];
                $add_url($meta[$key], '', $attrs);
            }
        }

        $property_images = $this->array_value($meta, 'property_images');
        foreach ($property_images as $image) {
            if (is_string($image)) {
                $add_url($image);
                continue;
            }
            if (!is_array($image)) {
                continue;
            }
            $url = isset($image['url']) ? (string) $image['url'] : '';
            if ($url === '') {
                continue;
            }
            $add_url($url, (string) ($image['caption'] ?? $image['tag'] ?? ''), [
                'tag' => $image['tag'] ?? '',
                'is_default' => !empty($image['is_default']),
                'is_house_main' => !empty($image['is_house_main']),
                'is_scheme' => !empty($image['is_scheme']),
                'is_plan' => !empty($image['is_plan']),
                'is_floor_plan' => !empty($image['is_floor_plan']),
            ]);
        }

        $thumbnail_id = (int) get_post_thumbnail_id($post_id);
        if ($thumbnail_id) {
            $add_attachment($thumbnail_id);
        }

        $attachments = get_children([
            'post_parent' => $post_id,
            'post_type' => 'attachment',
            'post_mime_type' => 'image',
            'posts_per_page' => 50,
            'orderby' => 'menu_order ID',
            'order' => 'ASC',
            'fields' => 'ids',
        ]);

        foreach ((array) $attachments as $attachment_id) {
            $add_attachment((int) $attachment_id);
        }

        return $photos;
    }

    private function flatten_meta(array $meta): array
    {
        $result = [];
        foreach ($meta as $key => $values) {
            $normalized_key = (string) $key;
            if (strpos($normalized_key, '_property_') === 0) {
                $normalized_key = substr($normalized_key, 1);
            } elseif (substr($normalized_key, 0, 1) === '_') {
                continue;
            }
            $value = is_array($values) && count($values) === 1 ? $values[0] : $values;
            $result[$normalized_key] = maybe_unserialize($value);
        }
        return $result;
    }

    private function collect_taxonomies(int $post_id): array
    {
        $result = [];
        $taxonomies = get_object_taxonomies(get_post_type($post_id), 'names');
        foreach ($taxonomies as $taxonomy) {
            $terms = wp_get_post_terms($post_id, $taxonomy);
            if (is_wp_error($terms)) {
                continue;
            }
            $result[$taxonomy] = array_map(static function (\WP_Term $term): array {
                return [
                    'id' => $term->term_id,
                    'name' => $term->name,
                    'slug' => $term->slug,
                ];
            }, $terms);
        }
        return $result;
    }

    private function first_value(array $acf, array $meta, array $keys): string
    {
        foreach ($keys as $key) {
            if (isset($acf[$key]) && $acf[$key] !== '') {
                return is_scalar($acf[$key]) ? (string) $acf[$key] : '';
            }
            if (isset($meta[$key]) && $meta[$key] !== '') {
                return is_scalar($meta[$key]) ? (string) $meta[$key] : '';
            }
        }
        return '';
    }

    private function array_value(array $meta, string $key): array
    {
        if (!isset($meta[$key]) || $meta[$key] === '') {
            return [];
        }
        return is_array($meta[$key]) ? $meta[$key] : [$meta[$key]];
    }

    private function match_first(string $text, string $pattern): string
    {
        if (preg_match($pattern, $text, $matches)) {
            return (string) $matches[1];
        }
        return '';
    }

    private function detect_deal_type(string $text, array $meta = []): string
    {
        $type = strtolower((string) ($meta['property_type'] ?? ''));
        if (in_array($type, ['аренда', 'rent'], true)) {
            return 'rent';
        }
        if (in_array($type, ['продажа', 'sale', 'sell'], true)) {
            return 'sale';
        }
        $text = mb_strtolower($text);
        if (preg_match('/аренд|снять/u', $text)) {
            return 'rent';
        }
        if (preg_match('/продаж|прода|купить/u', $text)) {
            return 'sale';
        }
        return '';
    }

    private function detect_segment(string $text, array $meta = []): string
    {
        $category = mb_strtolower((string) ($meta['property_category'] ?? ''));
        if (preg_match('/коммер|commercial/u', $category)) {
            return 'commercial';
        }
        $text = mb_strtolower($text);
        return preg_match('/офис|склад|помещ|коммер/u', $text) ? 'commercial' : 'residential';
    }

    private function features_from_text(string $text, array $acf, array $meta): array
    {
        $features = [];
        $configured = $this->first_value($acf, $meta, ['features', 'advantages']);
        if ($configured !== '') {
            $features = array_filter(array_map('trim', preg_split('/[\r\n;]+/', $configured)));
        }

        $lower = mb_strtolower($text);
        foreach ([
            'ремонт' => 'Помещение с ремонтом',
            'парков' => 'Есть парковка',
            'останов' => 'Рядом остановка транспорта',
            'транспорт' => 'Хорошая транспортная доступность',
            'интернет' => 'Подключен интернет',
        ] as $needle => $label) {
            if (mb_strpos($lower, $needle) !== false && !in_array($label, $features, true)) {
                $features[] = $label;
            }
        }

        return array_values(array_slice($features, 0, 10));
    }

    private function api_token(): string
    {
        return (string) get_option(self::OPTION_API_TOKEN, '');
    }
}

new Office_Presentations_Plugin();
