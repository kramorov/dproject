<?php
/**
 * Plugin Name: Каталог оборудования
 * Description: Встраивает каталог редукторов/приводов через шорткод [catalog]
 * Version: 1.0
 *
 * Использование:
 *   [catalog]                  — полный каталог (геarbox)
 *   [catalog type="gearbox"]   — только редукторы
 *   [catalog type="pneumatic"] — только пневмоприводы
 *
 * Настройка темы: админка → Настройки → Каталог → CSS-переменные
 */

// Защита от прямого доступа
if (!defined('ABSPATH')) exit;

// ═══ Шорткод ═══
function catalog_shortcode($atts) {
    $atts = shortcode_atts(['type' => 'gearbox'], $atts);
    $type = esc_attr($atts['type']);

    // URL dev-сервера Vite (заменить на production при деплое)
    $widget_url = 'http://localhost:5173/src/apps/widget/main.js';
    $theme_url  = 'http://localhost:5173/src/shared/themes/default.css';

    // Пользовательские CSS-переменные из настроек
    $custom_css = get_option('catalog_custom_css', '');

    ob_start();
    ?>
    <!-- Каталог оборудования -->
    <link rel="stylesheet" href="<?php echo esc_url($theme_url); ?>">
    <?php if ($custom_css): ?>
    <style>:root { <?php echo $custom_css; ?> }</style>
    <?php endif; ?>
    <div id="widget-root" data-catalog="<?php echo $type; ?>"></div>
    <script type="module" src="<?php echo esc_url($widget_url); ?>"></script>
    <?php
    return ob_get_clean();
}
add_shortcode('catalog', 'catalog_shortcode');

// ═══ Страница настроек ═══
function catalog_settings_init() {
    register_setting('catalog_options', 'catalog_custom_css');

    add_settings_section(
        'catalog_section',
        'Настройки каталога',
        function() {
            echo '<p>Переопределите CSS-переменные темы. Пример: --cat-primary: #dc2626; --cat-radius-lg: 0;</p>';
        },
        'catalog'
    );

    add_settings_field(
        'catalog_custom_css',
        'CSS-переменные',
        function() {
            $value = get_option('catalog_custom_css', '');
            echo '<textarea name="catalog_custom_css" rows="6" cols="50" class="large-text code">'
                . esc_textarea($value) . '</textarea>';
        },
        'catalog',
        'catalog_section'
    );
}
add_action('admin_init', 'catalog_settings_init');

function catalog_options_page() {
    add_options_page(
        'Каталог',
        'Каталог',
        'manage_options',
        'catalog',
        function() {
            echo '<div class="wrap"><h1>Настройки каталога</h1><form action="options.php" method="post">';
            settings_fields('catalog_options');
            do_settings_sections('catalog');
            submit_button();
            echo '</form></div>';
        }
    );
}
add_action('admin_menu', 'catalog_options_page');
